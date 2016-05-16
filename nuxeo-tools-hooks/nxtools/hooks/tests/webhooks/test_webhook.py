from flask.app import Flask
from nxtools import services
from nxtools.hooks.endpoints.webhook import WebHookEndpoint, NoSuchHookException
from nxtools.hooks.endpoints.webhook.github_handlers.push_notify_mail import GithubPushNotifyMailHandler
from nxtools.hooks.endpoints.webhook.github_hook import GithubHook, UnknownEventException, InvalidPayloadException
from nxtools.hooks.tests.case import HooksTestCase


class WebhooksTest(HooksTestCase):

    def setUp(self):
        super(WebhooksTest, self).setUp()
        self.flask = Flask(__name__)

    def test_routing(self):
        endpoint = services.get(WebHookEndpoint)
        """:type : WebHookEndpoint"""

        endpoint.add_handler(self.mocks.handler)

        with self.flask.test_request_context("/"):
            self.mocks.handler.can_handle.return_value = False
            with self.assertRaises(NoSuchHookException):
                endpoint.route()
            self.mocks.handler.can_handle.assert_called_once()
            self.mocks.handler.handle.assert_not_called()

            self.mocks.handler.can_handle.return_value = True
            endpoint.route()
            self.assertEqual(2, self.mocks.handler.can_handle.call_count)
            self.mocks.handler.handle.assert_called_once()

    def test_github(self):
        hook = GithubHook()
        hook.add_handler("push", GithubPushNotifyMailHandler())
        with self.assertRaises(UnknownEventException):
            hook.handle({GithubHook.payloadHeader: "Unknown"}, "{}")

        with self.assertRaises(InvalidPayloadException):
            hook.handle({GithubHook.payloadHeader: "push"}, "{}")

        # def testIssueComment(self):
    #     GithubHook.add_handler("issue_comment", GithubReviewHandler(self.handler))
    #
    #     self.mocks.commit.get_statuses.return_value = [
    #         Mock(state="success", raw_data={"context": "review/nuxeo"})
    #     ]
    #     self.mocks.pull_request.get_commits.return_value = Mock(reversed=[self.mocks.commit])
    #     self.mocks.repository.get_pull.return_value = self.mocks.pull_request
    #     self.mocks.organization.get_repo.return_value = self.mocks.repository
    #
    #     with GithubHandlerTest.payload_file('github_issue_comment') as payload:
    #         body, headers = payload
    #         self.handler.handle(headers, body)
