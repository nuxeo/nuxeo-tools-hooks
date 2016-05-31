from nxtools import services
from nxtools.hooks.endpoints.webhook.github_handlers.pullrequest_store import GithubStorePullRequestHandler
from nxtools.hooks.entities.github_entities import PullRequestEvent
from nxtools.hooks.entities.db_entities import StoredPullRequest
from nxtools.hooks.services.database import DatabaseService
from nxtools.hooks.tests.webhooks.github_handlers import GithubHookHandlerTest


class GithubStorePullRequestHandlerTest(GithubHookHandlerTest):

    def setUp(self):
        super(GithubStorePullRequestHandlerTest, self).setUp()

        services.get(DatabaseService).connect()

    @property
    def handler(self):
        """
        :rtype: nxtools.hooks.endpoints.webhook.github_handlers.pullrequest_store.GithubStorePullRequestHandler
        """
        return services.get(GithubStorePullRequestHandler)

    def test_store_pull_request(self):
        with GithubHookHandlerTest.payload_file('github_pullrequest_open') as payload:
            body = self.get_json_body_from_payload(payload)

            event = PullRequestEvent(None, None, body, True)

            self.assertEqual(body["action"], event.action)
            self.assertEqual(body["number"], event.number)
            self.assertEqual(body["pull_request"]["head"]["ref"], event.pull_request.head.ref)
            self.assertEqual(body["pull_request"]["head"]["sha"], event.pull_request.head.sha)
            self.assertEqual(body["repository"]["name"], event.repository.name)

            self.handler.handle(body)

            pull_requests = StoredPullRequest.objects(
                branch=event.pull_request.head.ref,
                repository=event.repository.name,
                head_commit=event.pull_request.head.sha
            )

            self.assertEqual(1, len(pull_requests))
            self.assertEqual(body["number"], pull_requests[0].pull_number)
            self.assertEqual(body["pull_request"]["head"]["ref"], pull_requests[0].branch)
            self.assertEqual(body["pull_request"]["head"]["sha"], pull_requests[0].head_commit)
            self.assertEqual(body["repository"]["name"], pull_requests[0].repository)
