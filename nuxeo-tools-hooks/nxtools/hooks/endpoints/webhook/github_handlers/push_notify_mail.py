"""
(C) Copyright 2016 Nuxeo SA (http://nuxeo.com/) and contributors.

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
"""

from importlib import import_module
from multiprocessing import Process

import gevent
import re
import logging

from jinja2.environment import Environment
from jinja2.loaders import PackageLoader
from nxtools import services, ServiceContainer
from nxtools.hooks.endpoints.webhook.github_handlers import AbstractGithubHandler
from nxtools.hooks.endpoints.webhook.github_hook import InvalidPayloadException, GithubHook
from nxtools.hooks.entities.github_entities import PushEvent
from nxtools.hooks.entities.mail import Email
from nxtools.hooks.services.github_service import GithubService
from nxtools.hooks.services.mail import EmailService
from unidecode import unidecode

log = logging.getLogger(__name__)


@ServiceContainer.service
class GithubPushNotifyMailHandler(AbstractGithubHandler):

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
        checks = self.get_config("ignore_checks", [])
        if checks:
            checks = re.sub(r"\s+", "", checks, flags=re.UNICODE).split(",")
        else:
            return [branch_ignore, suffix_ignore, repository_ignore]

        for i, check in enumerate(checks):
            module_str, function_str = check.rsplit('.', 1)
            module = import_module(module_str)
            checks[i] = getattr(module, function_str)

        return checks

    @property
    def ignored_branches(self):
        branches = self.get_config("ignored_branches", [])
        if branches:
            return re.sub(r"\s+", "", branches, flags=re.UNICODE).split(",")
        return branches

    @property
    def ignore_branch_suffixes(self):
        suffixes = self.get_config("ignored_branch_suffixes", [])
        if suffixes:
            return re.sub(r"\s+", "", suffixes, flags=re.UNICODE).split(",")
        return suffixes

    @property
    def ignore_repositories(self):
        repositories = self.get_config("ignored_repositories", [])
        if repositories:
            return re.sub(r"\s+", "", repositories, flags=re.UNICODE).split(",")
        return repositories

    @property
    def recipients(self):
        recipients = self.get_config("recipients", "ecm-checkins@lists.nuxeo.com")
        if recipients:
            return re.sub(r"\s+", "", recipients, flags=re.UNICODE).split(",")
        return recipients

    @property
    def recipients_priv(self):
        recipients = self.get_config("recipients_priv", "interne-checkins@lists.nuxeo.com")
        if recipients:
            return re.sub(r"\s+", "", recipients, flags=re.UNICODE).split(",")
        return recipients

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

    def can_handle(self, payload_event):
        return "push" == payload_event

    def handle(self, payload_body):
        event = PushEvent(None, None, payload_body, True)
        email_service = services.get(EmailService)

        if self.is_bad_ref(event):
            return 400, GithubPushNotifyMailHandler.MSG_BAD_REF % event.ref

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
        :type commit: nxtools.hooks.entities.github_entities.Commit
        :rtype: nxtools.hooks.entities.mail.Email
        """
        template = self._jinja.get_template(self.email_template)
        committer_name = commit.committer.name
        pusher = None
        jira_tickets = []

        if self.is_jenkins(event) and commit.committer.email != self.jenkins_email:
            committer_name += " via Jenkins"

        real_address = u"%s <%s>" % (committer_name, commit.committer.email)
        fake_address = u"%s <%s>" % (committer_name, self.sender)

        if event.pusher.email and commit.committer.email and event.pusher.email != commit.committer.email:
            pusher = "%s <%s>" % (event.pusher.name, event.pusher.email)

        for match in self.jira_regex.finditer(commit.message):
            jira_tickets.append(match.group(1).upper())

        try:
            diff = services.get(GithubService).get_organization(event.organization.login).get_repo(event.repository.name).\
                get_commit_diff(commit.id)
        except Exception as e:
            diff = "Could not read diff - see %s.diff for raw diff" % commit.url
            diff += "\n(Error: %s)\n" % (str(e))

        subject = u"%s: %s (branch@%s)" % (event.repository.name, commit.message, self.get_branch_short_name(event))

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
    addWarn = False
    if event.repository.name in handler.ignore_repositories:
        has_system = False
        has_non_system = False
        ignored_urls = []
        for commit in event.commits:
            if re.match(".*updated by SYSTEM.*", commit.message):
                has_system = True
                ignored_urls.append(commit.url)
            else:
                has_non_system = True
        if has_system and not has_non_system:
            if handler.is_jenkins(event):
                return True, False, GithubPushNotifyMailHandler.MSG_IGNORE_COMMITS % (", ".join(ignored_urls))
            else:
                addWarn = True
    return False, addWarn, None


