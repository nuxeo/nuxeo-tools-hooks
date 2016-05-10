
import json

from mock.mock import patch, Mock, PropertyMock
from nxtools.hooks.tests.case import HooksTestCase
from nxtools.hooks.webhook.github_handlers.push_notify_mail import GithubPushNotifyMailHandler
from nxtools.hooks.webhook.github_hook import GithubHook, UnknownEventException, InvalidPayloadException


class GithubHandlerTest(HooksTestCase):

    class payload_file(object):

        def __init__(self, filename):
            self.filename = filename
            self.payload_file = None
            self.headers_file = None

        def __enter__(self):
            self.payload_file = open('nxtools/hooks/tests/resources/github_hooks/%s.json' % self.filename)
            self.headers_file = open('nxtools/hooks/tests/resources/github_hooks/%s.headers.json' % self.filename)
            return self.payload_file.read(), json.load(self.headers_file)

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.payload_file.close()
            self.headers_file.close()

    def setUp(self):
        self.mocks = GithubHandlerTest.TestMocks()

        self.hook = GithubHook()
        self.maxDiff = None

        patcher_organization = patch('github.MainClass.Github.get_organization', return_value=self.mocks.organization)

        patcher_organization.start()

        # Mocks required for nxtools.hooks.entities.github_entities.RepositoryWrapper#get_commit_diff
        self.mocks.repository_url = PropertyMock(return_value="http://null.void/")
        type(self.mocks.organization.get_repo.return_value).url = self.mocks.repository_url
        self.mocks.requester.requestJson.return_value = "Query mocked"
        self.mocks.organization.get_repo.return_value._requester = self.mocks.requester

        self.addCleanup(patcher_organization.stop)

    def test_event(self):
        self.hook.add_handler("push", GithubPushNotifyMailHandler(self.hook, Mock()))
        with self.assertRaises(UnknownEventException):
            self.hook.handle({GithubHook.payloadHeader: "Unknown"}, "{}")

        with self.assertRaises(InvalidPayloadException):
            self.hook.handle({GithubHook.payloadHeader: "push"}, "{}")

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
