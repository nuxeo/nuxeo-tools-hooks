"""
(C) Copyright 2016 Nuxeo SA (http://nuxeo.com/) and contributors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
you may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Contributors:
    Pierre-Gildas MILLON <pgmillon@nuxeo.com>
    Anahide Tchertchian <at@nuxeo.com>
"""

from github.PullRequest import PullRequest
from github.Commit import Commit
from nose.tools import nottest
from nxtools import services
from nxtools.hooks.endpoints.webhook.github_handlers.pull_request import GithubStorePullRequestHandler
from nxtools.hooks.entities.github_entities import PullRequestEvent
from nxtools.hooks.entities.db_entities import StoredPullRequest
from nxtools.hooks.services.config import Config
from nxtools.hooks.services.database import DatabaseService
from nxtools.hooks.tests.webhooks.github_handlers import GithubHookHandlerTest


class MockPullRequest(PullRequest):

    class MockedPaginatedList(list):
        @property
        def reversed(self):
            self.reverse()
            return self

    def __init__(self, pr, commits):
        PullRequest.__init__(self, None, {}, pr, True)
        self._commits = commits
        self._comment = None

    def get_commits(self):
        res = MockPullRequest.MockedPaginatedList()
        for commit in self._commits:
            res.append(Commit(None, {}, commit, True))
        return res

    def create_issue_comment(self, comment):
        self._comment = comment

class GithubStorePullRequestHandlerTest(GithubHookHandlerTest):

    def setUp(self):
        super(GithubStorePullRequestHandlerTest, self).setUp()
        services.get(DatabaseService).connect()

    def tearDown(self):
        super(GithubStorePullRequestHandlerTest, self).tearDown()
        StoredPullRequest.drop_collection()

    @property
    def handler(self):
        """
        :rtype: nxtools.hooks.endpoints.webhook.github_handlers.pull_request.GithubStorePullRequestHandler
        """
        return services.get(GithubStorePullRequestHandler)

    @property
    def config(self):
        """
        :rtype: nxtools.hooks.services.config.Config
        """
        return services.get(Config)

    def test_store_pull_request(self):
        with GithubHookHandlerTest.payload_file('github_pullrequest_open') as payload:
            body = self.get_json_body_from_payload(payload)

            event = PullRequestEvent(None, None, body, True)

            self.assertEqual(body["action"], event.action)
            self.assertEqual(body["number"], event.number)
            self.assertEqual(body["pull_request"]["head"]["ref"], event.pull_request.head.ref)
            self.assertEqual(body["pull_request"]["head"]["sha"], event.pull_request.head.sha)
            self.assertEqual(body["repository"]["name"], event.repository.name)

            self.handler._do_handle(body)

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

    def mock_get_pull(self, id):
        return self.mocks.pr

    def test_store_pull_request_trigger_review(self):
        self.config._config.set("GithubReviewService", "active", "true")
        with GithubHookHandlerTest.payload_file('github_pullrequest_open') as payload, \
            GithubHookHandlerTest.payload_file('github_pullrequest') as prp, \
            GithubHookHandlerTest.payload_file('github_pullrequest_commits') as prc:
            body = self.get_json_body_from_payload(payload)
            pr = self.get_json_body_from_payload(prp)
            commits = self.get_json_body_from_payload(prc)
            self.mocks.pr = MockPullRequest(pr, commits)
            self.mocks.organization.get_repo.return_value.get_pull = self.mock_get_pull

            self.handler._do_handle(body)

            self.assertEqual("[View issue in JIRA](https://jira.nuxeo.com/browse/NXP-20340)", self.mocks.pr._comment)