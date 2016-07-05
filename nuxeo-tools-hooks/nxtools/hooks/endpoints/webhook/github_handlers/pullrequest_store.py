from nxtools import ServiceContainer, services
from nxtools.hooks.endpoints.webhook.github_handlers import AbstractGithubHandler
from nxtools.hooks.entities.github_entities import PullRequestEvent
from nxtools.hooks.services.github_service import GithubService


@ServiceContainer.service
class GithubStorePullRequestHandler(AbstractGithubHandler):

    MSG_OK = "OK"

    def can_handle(self, payload_event):
        return "pull_request" == payload_event

    def handle(self, payload_body):
        event = PullRequestEvent(None, None, payload_body, True)
        services.get(GithubService).create_pullrequest(event.organization, event.repository, event.pull_request)

        return 200, GithubStorePullRequestHandler.MSG_OK
