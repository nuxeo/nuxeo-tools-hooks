from nxtools.hooks.endpoints.github_hook import AbstractGithubHandler
from nxtools.hooks.entities.github_entities import PullRequestEvent
from nxtools.hooks.entities.nuxeo_qa import StoredPullRequest


class GithubStorePullRequestHandler(AbstractGithubHandler):

    def __init__(self, hook, db_service):
        """
        :type hook : nxtools.hooks.endpoints.github_hook.GithubHookEndpoint
        :type db_service : nxtools.hooks.services.database.DatabaseService
        """
        super(GithubStorePullRequestHandler, self).__init__(hook)

        self._db_service = db_service

    def handle(self, payload_body):
        event = PullRequestEvent(None, None, payload_body, True)

        stored_pr = StoredPullRequest(
            branch=event.pull_request.head.ref,
            repository=event.repository.name,
            head_commit=event.pull_request.head.sha,
            pull_number=event.number
        )

        stored_pr.save()


