"""
(C) Copyright 2016-2020 Nuxeo SA (http://nuxeo.com/) and contributors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
you may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Contributors:
    Pierre-Gildas MILLON <pgmillon@nuxeo.com>
    Anahide Tchertchian <at@nuxeo.com>
"""

from importlib import import_module
from multiprocessing import Process

import gevent
import re
import logging

from jinja2.environment import Environment
from jinja2.loaders import PackageLoader
from nxtools import services, ServiceContainer
from nxtools.hooks.endpoints.webhook.github_handlers import AbstractGithubJsonHandler
from nxtools.hooks.endpoints.webhook.github_hook import InvalidPayloadException, GithubHook
from nxtools.hooks.entities.github_entities import PushEvent
from nxtools.hooks.entities.mail import Email
from nxtools.hooks.services.github_service import GithubService
from nxtools.hooks.services.mail import EmailService
from unidecode import unidecode

log = logging.getLogger(__name__)


@ServiceContainer.service
class GithubPushNotifyMailHandler(AbstractGithubJsonHandler):

    MSG_BAD_REF = "Unknown branch reference '%s'"
    MSG_IGNORE_BRANCH = "Ignore branch '%s'"
    MSG_IGNORE_COMMITS = "Ignore commits %s"
    MSG_OK = "OK"

    JENKINS_PUSHER_NAME = "nuxeojenkins"

    def __init__(self):
        super(GithubPushNotifyMailHandler, self).__init__()

        self._jinja = Environment(loader=PackageLoader(GithubPushNotifyMailHandler.__module__, 'resources'))

    @property
    def ignore_checks(self):
        checks = self.get_config_list("ignore_checks", [])
        if not checks:
            return [branch_ignore, suffix_ignore, repository_ignore]

        for i, check in enumerate(checks):
            module_str, function_str = check.rsplit('.', 1)
            module = import_module(module_str)
            checks[i] = getattr(module, function_str)

        return checks

    @property
    def ignored_branches(self):
        return self.get_config_list("ignored_branches", [])

    @property
    def ignore_branch_suffixes(self):
        return self.get_config_list("ignored_branch_suffixes", [])

    @property
    def ignore_repositories(self):
        return self.get_config_list("ignored_repositories", [])

    @property
    def whitelisted_private_repositories(self):
        return self.get_config_list('whitelisted_private_repositories', [])

    @property
    def recipients(self):
        return self.get_config_list("recipients", "ecm-checkins@lists.nuxeo.com")

    @property
    def recipients_priv(self):
        return self.get_config_list("recipients_priv", "interne-checkins@lists.nuxeo.com")

    @property
    def jenkins_name(self):
        return self.get_config("jenkins_name", "Jenkins Nuxeo")

    @property
    def jenkins_username(self):
        return self.get_config("jenkins_username", "nuxeojenkins")

    @property
    def jenkins_email(self):
        return self.get_config("jenkins_email", "jenkins@nuxeo.com")

    @property
    def sender(self):
        return self.get_config("sender", "noreply@nuxeo.com")

    @property
    def jira_regex(self):
        return re.compile(self.get_config("jira_regex", r"\b([A-Z]+-\d+)\b"), re.I)

    @property
    def email_template(self):
        return self.get_config("jinja_template", "notify_mail.txt")

    def can_handle(self, headers, body):
        return "push" == headers[GithubHook.payloadHeader]

    def _do_handle(self, payload_body):
        log.info('GithubPushNotifyMailHandler.handle')
        event = PushEvent(None, None, payload_body, True)
        email_service = services.get(EmailService)

        if self.is_bad_ref(event):
            log.info("Unhandled ref: %s/%s:%s",
                     event.organization.login,
                     event.repository.name,
                     event.ref)
            return 200, GithubPushNotifyMailHandler.MSG_BAD_REF % event.ref

        should_exit, add_warn, exit_message = self.check_branch_ignored(event)

        if should_exit:
            return 200, exit_message

        def create_and_send(commit):
            try:
                email = self.get_commit_email(event, commit, add_warn)
                Process(target=lambda: email_service.sendemail(email)).start()
            except Exception as e:
                log.warn("Failed to create email for commit: %s", commit.url)
                raise e

        gevent.joinall([gevent.spawn(create_and_send, commit) for commit in event.commits])

        return 200, GithubPushNotifyMailHandler.MSG_OK

    def is_jenkins(self, event):
        """
        :type event: nxtools.hooks.entities.github_entities.PushEvent
        """
        return event.pusher.name == self.jenkins_username

    def is_bad_ref(self, event):
        """
        :type event: nxtools.hooks.entities.github_entities.PushEvent
        """
        if not event.ref:
            raise InvalidPayloadException(None)

        return not event.ref.startswith("refs/heads/")

    def get_branch_short_name(self, event):
        """
        :type event: nxtools.hooks.entities.github_entities.PushEvent
        """
        if not event.ref:
            raise InvalidPayloadException(None)

        return event.ref[11:]

    def get_commit_email(self, event, commit, with_warn):
        """
        :type event: nxtools.hooks.entities.github_entities.PushEvent
        :type commit: nxtools.hooks.entities.github_entities.PushEventCommit
        :rtype: nxtools.hooks.entities.mail.Email
        """
        template = self._jinja.get_template(self.email_template)
        author_name = commit.author.name
        author_email = commit.author.email
        pusher = None
        jira_tickets = []

        if self.is_jenkins(event) and author_email != self.jenkins_email:
            author_name += " via Jenkins"

        real_address = u"%s <%s>" % (author_name, author_email)
        fake_address = u"%s <%s>" % (author_name, self.sender)

        if event.pusher.email and author_email and event.pusher.email != author_email:
            pusher = "%s <%s>" % (event.pusher.name, event.pusher.email)

        for match in self.jira_regex.finditer(commit.message):
            ticket = match.group(1).upper()
            if ticket not in jira_tickets:
                jira_tickets.append(ticket)

        try:
            diff = services.get(GithubService).get_organization(event.organization.login).get_repo(event.repository.name).\
                get_commit_diff(commit.id)
        except Exception as e:
            diff = "Could not read diff - see %s.diff for raw diff" % commit.url
            diff += "\n(Error: %s)\n" % (str(e))

        subject = u"%s: %s (branch@%s)" % (event.repository.name, commit.message.splitlines()[0], self.get_branch_short_name(event))

        if with_warn:
            subject = "[WARN] " + subject

        recipients = self.recipients
        if event.repository.private:
            recipients = self.recipients_priv

        return Email(body=template.render(
            commit_message=commit.message,
            repository=event.repository.name,
            branch=self.get_branch_short_name(event),
            author=real_address,
            commit_date=commit.timestamp,
            commit_url=commit.url,
            commit_added=commit.added,
            commit_removed=commit.removed,
            commit_modified=commit.modified,
            with_pusher=pusher,
            with_warn=with_warn,
            jira_tickets=jira_tickets,
            diff=diff
        ), subject=unidecode(subject), sender=unidecode(fake_address), reply_to=unidecode(real_address), to=recipients)

    def check_branch_ignored(self, event):
        """
        :type event: nxtools.hooks.entities.github_entities.PushEvent
        """
        warn = False
        for check in self.ignore_checks:
            should_exit, add_warn, exit_message = check(self, event)
            warn = warn or add_warn
            if should_exit:
                return should_exit, warn, exit_message
        return False, warn, None


def branch_ignore(handler, event):
    """
    :type handler: nxtools.hooks.endpoints.webhook.github_handlers.push_notify_mail.GithubPushNotifyMailHandler
    :type event: nxtools.hooks.entities.github_entities.PushEvent
    """
    branch = handler.get_branch_short_name(event)

    if branch in handler.ignored_branches:
        if handler.is_jenkins(event):
            return True, False, GithubPushNotifyMailHandler.MSG_IGNORE_BRANCH % branch
        return False, True, ""
    return False, False, None


def suffix_ignore(handler, event):
    """
    :type handler: nxtools.hooks.endpoints.webhook.github_handlers.push_notify_mail.GithubPushNotifyMailHandler
    :type event: nxtools.hooks.entities.github_entities.PushEvent
    """
    branch = handler.get_branch_short_name(event)

    for suffix in handler.ignore_branch_suffixes:
        if branch.endswith(suffix):
            if handler.is_jenkins(event):
                return True, False, GithubPushNotifyMailHandler.MSG_IGNORE_BRANCH % branch
            return False, True, ""
    return False, False, None


def repository_ignore(handler, event):
    """
    :type handler: nxtools.hooks.endpoints.webhook.github_handlers.push_notify_mail.GithubPushNotifyMailHandler
    :type event: nxtools.hooks.entities.github_entities.PushEvent
    """
    key = "%s/%s" % (event.organization.login, event.repository.name)
    return key in handler.ignore_repositories or (event.repository.private and key not in handler.whitelisted_private_repositories), False, None

