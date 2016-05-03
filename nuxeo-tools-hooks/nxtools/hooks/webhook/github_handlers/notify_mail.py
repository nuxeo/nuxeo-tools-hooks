from nxtools.hooks.entities.github.PushEvent import PushEvent
from nxtools.hooks.webhook.github_hook import AbstractGithubHandler


class GithubNotifyMailHandler(AbstractGithubHandler):

    MSG_BAD_REF = "Unknown branch reference '%s'"

    def handle(self, payload_body):
        event = PushEvent(None, None, payload_body, True)

        is_jenkins = event.pusher.name == "nuxeojenkins"
        is_bad_ref = not event.ref.startswith("refs/heads/")

        if is_bad_ref:
            return 400, GithubNotifyMailHandler.MSG_BAD_REF % event.ref

