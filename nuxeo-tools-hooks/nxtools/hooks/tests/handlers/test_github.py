
import unittest
import json

from mock.mock import patch, Mock
from nxtools.hooks.webhook.github_handlers.notify_mail import GithubNotifyMailHandler
from nxtools.hooks.webhook.github_handlers.review import GithubReviewHandler
from nxtools.hooks.webhook.github_hook import GithubHook, UnknownEventException, InvalidPayloadException


class GithubHandlerTest(unittest.TestCase):

    class TestMocks(object):

        def __init__(self):
            self._items = {}

        def __getattribute__(self, item):
            items = object.__getattribute__(self, '_items')
            if item not in items:
                items[item] = Mock()
            return items[item]

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

        self.handler = GithubHook()

        patcher_organization = patch('nxtools.hooks.webhook.github_hook.GithubHook.organization',
                                     self.mocks.organization)

        patcher_organization.start()
        self.addCleanup(patcher_organization.stop)

    def test_event(self):
        with self.assertRaises(UnknownEventException):
            self.handler.handle({GithubHook.payloadHeader: "Unknown"}, "{}")

        with self.assertRaises(InvalidPayloadException):
            self.handler.handle({GithubHook.payloadHeader: "issue_comment"}, "{}")

    def testSendEmail(self):
        with GithubHandlerTest.payload_file('github_push') as payload:
            raw_body, headers = payload

            body = json.loads(raw_body)
            bad_ref_body = body.copy()
            bad_ref_body["ref"] = "refs/wrong/anything"
            self.assertTupleEqual((400, GithubNotifyMailHandler.MSG_BAD_REF % bad_ref_body["ref"]),
                                  GithubNotifyMailHandler(self.handler).handle(bad_ref_body))

            jenkins_author_body = body.copy()
            jenkins_author_body["pusher"]["name"] = GithubNotifyMailHandler.JENKINS_PUSHER_NAME
            explicit_ignore_handler = GithubNotifyMailHandler(self.handler)
            explicit_ignore_handler._ignored_branches = ['feature-NXBT-1074-hooks-refactoring']
            self.assertTupleEqual((200, GithubNotifyMailHandler.MSG_IGNORE_BRANCH % body["ref"][11:]),
                                  explicit_ignore_handler.handle(jenkins_author_body))

    def testIssueComment(self):
        GithubHook.add_handler("issue_comment", GithubReviewHandler(self.handler))

        self.mocks.commit.get_statuses.return_value = [
            Mock(state="success", raw_data={"context": "review/nuxeo"})
        ]
        self.mocks.pull_request.get_commits.return_value = Mock(reversed=[self.mocks.commit])
        self.mocks.repository.get_pull.return_value = self.mocks.pull_request
        self.mocks.organization.get_repo.return_value = self.mocks.repository

        with GithubHandlerTest.payload_file('github_issue_comment') as payload:
            body, headers = payload
            self.handler.handle(headers, body)
