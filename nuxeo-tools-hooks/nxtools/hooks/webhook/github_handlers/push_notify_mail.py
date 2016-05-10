
import re

from jinja2.environment import Environment
from jinja2.loaders import PackageLoader
from nxtools.hooks.entities.mail import Email
from nxtools.hooks.entities.github_entities import PushEvent
from nxtools.hooks.webhook.github_hook import AbstractGithubHandler, InvalidPayloadException
from unidecode import unidecode


class GithubPushNotifyMailHandler(AbstractGithubHandler):

    MSG_BAD_REF = "Unknown branch reference '%s'"
    MSG_IGNORE_BRANCH = "Ignore branch '%s'"
    MSG_IGNORE_COMMITS = "Ignore commits %s"
    MSG_OK = "OK"

    JENKINS_PUSHER_NAME = "nuxeojenkins"

    def __init__(self, hook, email_service):
        """
        :type hook : nxtools.hooks.webhook.github_hook.GithubHook
        :type email_service : nxtools.hooks.services.mail.EmailService
        """
        super(GithubPushNotifyMailHandler, self).__init__(hook)

        self._email_service = email_service

        self._ignore_branch_checks = [
            self.branch_ignore,
            self.suffix_ignore,
            self.repository_ignore
        ] #TODO: load from configuration file

        self._jinja = Environment(loader=PackageLoader(GithubPushNotifyMailHandler.__module__, 'resources'))
        self._ignored_branches = [] #TODO: load from configuration file
        self._ignored_branch_suffixes = [] #TODO: load from configuration file
        self._ignored_repositories = [] #TODO: load from configuration file
        self._sender = "noreply@nuxeo.com" #TODO: load from configuration file
        self._recipients = ["ecm-checkins@lists.nuxeo.com"] #TODO: load from configuration file
        self._jenkins_email = "jenkins@nuxeo.com" #TODO: load from configuration file
        self._jenkins_name = "Jenkins Nuxeo" #TODO: load from configuration file
        self._jenkins_username = "nuxeojenkins" #TODO: load from configuration file
        self._jinja_template = "notify_mail.txt" #TODO: load from configuration file
        self._jira_regex = re.compile(r"\b([A-Z]+-\d+)\b", re.I) #TODO: load from configuration file

    @property
    def ignored_branches(self):
        return self._ignored_branches

    @property
    def ignore_branch_suffixes(self):
        return self._ignored_branch_suffixes

    @property
    def ignore_repositories(self):
        return self._ignored_repositories

    @property
    def jenkins_name(self):
        return self._jenkins_name

    @property
    def jenkins_username(self):
        return self._jenkins_username

    @property
    def jenkins_email(self):
        return self._jenkins_email

    @property
    def sender(self):
        return self._sender

    @property
    def jira_regex(self):
        return self._jira_regex

    def handle(self, payload_body):
        event = PushEvent(None, None, payload_body, True)

        if self.is_bad_ref(event):
            return 400, GithubPushNotifyMailHandler.MSG_BAD_REF % event.ref

        should_exit, add_warn, exit_message = self.check_branch_ignored(event)

        if should_exit:
            return 200, exit_message

        for commit in event.commits:
            email = self.get_commit_email(event, commit, add_warn)
            self._email_service.sendemail(email)

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
        :rtype: nxtools.hooks.entities.github_entities.Email
        """
        template = self._jinja.get_template('notify_mail.txt')
        committer_name = commit.committer.name
        pusher = None
        jira_tickets = []

        if self.is_jenkins(event) and commit.committer.email != self._jenkins_email:
            committer_name += " via Jenkins"

        real_address = "%s <%s>" % (committer_name, commit.committer.email)
        fake_address = "%s <%s>" % (committer_name, self.sender)

        if event.pusher.email and commit.committer.email and event.pusher.email != commit.committer.email:
            pusher = "%s <%s>" % (event.pusher.name, event.pusher.email)

        for match in self.jira_regex.finditer(commit.message):
            jira_tickets.append(match.group(1).upper())

        try:
            diff = self.hook.get_organization(event.organization.login).get_repo(event.repository.name).\
                get_commit_diff(commit.id)
        except Exception as e:
            diff = "Could not read diff - see %s.diff for raw diff" % commit.url
            diff += "\n(Error: %s)\n" % (str(e))

        subject = "%s: %s (branch@%s)" % (event.repository.name, commit.message, self.get_branch_short_name(event))

        if with_warn:
            subject = "[WARN] " + subject

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
        ), subject=unidecode(subject), sender=unidecode(fake_address), reply_to=unidecode(real_address), to=None)

    def check_branch_ignored(self, event):
        """
        :type event: nxtools.hooks.entities.github_entities.PushEvent
        """
        warn = False
        for check in self._ignore_branch_checks:
            should_exit, add_warn, exit_message = check(event)
            warn = warn or add_warn
            if should_exit:
                return should_exit, warn, exit_message
        return False, warn, None

    def branch_ignore(self, event):
        """
        :type event: nxtools.hooks.entities.github_entities.PushEvent
        """
        branch = self.get_branch_short_name(event)

        if branch in self.ignored_branches:
            if self.is_jenkins(event):
                return True, False, GithubPushNotifyMailHandler.MSG_IGNORE_BRANCH % branch
            return False, True, ""
        return False, False, None

    def suffix_ignore(self, event):
        """
        :type event: nxtools.hooks.entities.github_entities.PushEvent
        """
        branch = self.get_branch_short_name(event)

        for suffix in self.ignore_branch_suffixes:
            if branch.endswith(suffix):
                if self.is_jenkins(event):
                    return True, False, GithubPushNotifyMailHandler.MSG_IGNORE_BRANCH % branch
            return False, True, ""
        return False, False, None

    def repository_ignore(self, event):
        """
        :type event: nxtools.hooks.entities.github_entities.PushEvent
        """
        addWarn = False
        if event.repository.name in self.ignore_repositories:
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
                if self.is_jenkins(event):
                    return True, False, GithubPushNotifyMailHandler.MSG_IGNORE_COMMITS % (", ".join(ignored_urls))
                else:
                    addWarn = True
        return False, addWarn, None


