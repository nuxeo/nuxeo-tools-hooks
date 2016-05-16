from nxtools.hooks.endpoints.webhook.github_handlers import AbstractGithubHandler
from nxtools.hooks.entities.github_entities import PullRequestEvent
from nxtools.hooks.entities.nuxeo_qa import StoredPullRequest


class GithubStorePullRequestHandler(AbstractGithubHandler):

    MSG_OK = "OK"

    def __init__(self, hook):
        """
        :type hook : nxtools.hooks.endpoints.github_hook.GithubHookEndpoint
        """
        super(GithubStorePullRequestHandler, self).__init__(hook)

    def handle(self, payload_body):
        event = PullRequestEvent(None, None, payload_body, True)

        stored_pr = StoredPullRequest(
            branch=event.pull_request.head.ref,
            repository=event.repository.name,
            head_commit=event.pull_request.head.sha,
            pull_number=event.number
        )

        stored_pr.save()

        return 200, GithubStorePullRequestHandler.MSG_OK