from nxtools.hooks.entities.github.PushEvent import PushEvent
from nxtools.hooks.webhook.github_hook import AbstractGithubHandler


class GithubPushNotifyMailHandler(AbstractGithubHandler):

    MSG_BAD_REF = "Unknown branch reference '%s'"
    MSG_IGNORE_BRANCH = "Ignore branch '%s'"

    JENKINS_PUSHER_NAME = "nuxeojenkins"

    def __init__(self, hook):
        super(GithubPushNotifyMailHandler, self).__init__(hook)

        self._ignore_branch_checks = [
            self.explicit_ignore,
            self.suffix_ignore
        ] #TODO: load from configuration file

        self._ignored_branches = [] #TODO: load from configuration file
        self._ignored_branch_suffixes = [] #TODO: load from configuration file
        self._sender = "noreply@nuxeo.com" #TODO: load from configuration file
        self._recipients = ["ecm-checkins@lists.nuxeo.com"] #TODO: load from configuration file

    @property
    def ignored_branches(self):
        return self._ignored_branches

    @property
    def ignore_branch_suffixes(self):
        return self._ignored_branch_suffixes

    def handle(self, payload_body):
        event = PushEvent(None, None, payload_body, True)

        if self.is_bad_ref(event):
            return 400, GithubPushNotifyMailHandler.MSG_BAD_REF % event.ref

        should_exit, add_warn, exit_message = self.check_branch_ignored(event)

        if should_exit:
            return 200, exit_message

        return 200, "OK"

    def is_jenkins(self, event):
        return event.pusher.name.value == GithubPushNotifyMailHandler.JENKINS_PUSHER_NAME

    def is_bad_ref(self, event):
        return not event.ref.startswith("refs/heads/")

    def get_branch_short_name(self, event):
        return event.ref[11:]

    def check_branch_ignored(self, event):
        warn = False
        for check in self._ignore_branch_checks:
            should_exit, add_warn, exit_message = check(event)
            warn = warn or add_warn
            if should_exit:
                return should_exit, warn, exit_message
        return False, warn, None

    def explicit_ignore(self, event):
        branch = self.get_branch_short_name(event)

        if branch in self.ignored_branches:
            if self.is_jenkins(event):
                return True, False, GithubPushNotifyMailHandler.MSG_IGNORE_BRANCH % branch
            return False, True, ""
        return False, False, None

    def suffix_ignore(self, event):
        branch = self.get_branch_short_name(event)

        for suffix in self.ignore_branch_suffixes:
            if branch.endswith(suffix):
                if self.is_jenkins(event):
                    return True, False, GithubPushNotifyMailHandler.MSG_IGNORE_BRANCH % branch
            return False, True, ""
        return False, False, None


