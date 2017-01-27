# -*- coding: utf-8 -*-
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
"""
import json

from github.Commit import Commit
from github.CommitStatus import CommitStatus
from github.File import File
from github.NamedUser import NamedUser
from mock.mock import patch
from nxtools import services
from nxtools.hooks.endpoints.webhook.github_handlers.pullrequest_review import GithubReviewNotifyHandler, \
    GithubReviewService, GithubReviewCommentHandler
from nxtools.hooks.entities.db_entities import StoredPullRequest
from nxtools.hooks.entities.github_entities import PullRequestEvent, IssueCommentEvent
from nxtools.hooks.services.config import Config
from nxtools.hooks.services.database import DatabaseService
from nxtools.hooks.tests.webhooks.github_handlers import GithubHookHandlerTest


class GithubReviewPullRequestHandlerTest(GithubHookHandlerTest):

    def setUp(self):
        super(GithubReviewPullRequestHandlerTest, self).setUp()

        services.get(DatabaseService).connect()

    def tearDown(self):
        super(GithubReviewPullRequestHandlerTest, self).tearDown()

        StoredPullRequest.drop_collection()

    def mocked_in_members(self, username):
        self.assertIsInstance(username, NamedUser)
        return username.login in ['mguillaume', 'jcarsique', 'efge', 'tmartins']

    def mocked_get_user(self, username):
        return NamedUser(None, None, {"login": username}, True)

    @property
    def handler(self):
        """
        :rtype: nxtools.hooks.endpoints.webhook.github_handlers.pullrequest_review.GithubReviewNotifyHandler
        """
        return services.get(GithubReviewNotifyHandler)

    def test_open_pull_request(self):
        with GithubHookHandlerTest.payload_file('github_pullrequest_open') as payload:
            body = self.get_json_body_from_payload(payload)

        review_service = services.get(GithubReviewService)  # type: GithubReviewService
        event = PullRequestEvent(None, None, body, True)

        self.assertEqual(body["action"], event.action)
        self.assertEqual(body["number"], event.number)
        self.assertEqual(body["pull_request"]["head"]["ref"], event.pull_request.head.ref)
        self.assertEqual(body["pull_request"]["head"]["sha"], event.pull_request.head.sha)
        self.assertEqual(body["repository"]["name"], event.repository.name)

        with open('nxtools/hooks/tests/resources/github_handlers/github_pullrequest_open.files.json') as files_json:
            self.mocks.files = [File(None, None, raw_file, True) for raw_file in json.load(files_json)]

        with open('nxtools/hooks/tests/resources/github_handlers/github_blame.html') as blame_file:
            blame = review_service.parse_blame(blame_file.read())

        self.mocks.commits = []

        self.mocks.organization.get_repo.return_value.html_url = 'http://void.null/'
        self.mocks.organization.get_repo.return_value.get_pull.return_value.number = 42
        self.mocks.organization.get_repo.return_value.get_pull.return_value.get_files.return_value = self.mocks.files
        self.mocks.organization.get_repo.return_value.get_pull.return_value.get_commits.return_value = \
            self.mocks.commits
        self.mocks.organization.has_in_members.side_effect = self.mocked_in_members

        review_service.parse_patch(self.mocks.files[2].patch)
        deletions = review_service.parse_patch(self.mocks.files[1].patch)

        self.assertEqual(3, len(deletions))

        self.assertEqual(1614, len([l for l in blame if l == 'jcarsique']))
        self.assertEqual(127, len([l for l in blame if l == 'mguillaume']))
        self.assertEqual(67, len([l for l in blame if l == 'efge']))
        self.assertEqual(46, len([l for l in blame if l == 'atchertchian']))

        patchers = [
            patch('nxtools.hooks.endpoints.webhook.github_handlers.pullrequest_review.GithubReviewService.parse_patch',
                  return_value=deletions),
            patch(
                'nxtools.hooks.endpoints.webhook.github_handlers.pullrequest_review.GithubReviewService.parse_blame',
                return_value=blame),
            patch('nxtools.hooks.entities.github_entities.RepositoryWrapper.get_blame', return_value=None),
            patch('nxtools.hooks.services.github_service.Github.get_user', side_effect=self.mocked_get_user)
        ]

        [patcher.start() for patcher in patchers]

        self.assertListEqual(['jcarsique', 'mguillaume', 'efge'], review_service.get_owners(event))

        self.mocks.commits += [Commit(None, None, {
            "author": {"login": "jcarsique"}
        }, True), Commit(None, None, {
            "author": {"login": "efge"}
        }, True)]

        self.assertListEqual(['mguillaume', 'atchertchian', 'tmartins'], review_service.get_owners(event))

        services.get(Config).set_request_environ({
            Config.ENV_PREFIX + 'GITHUBREVIEW_REQUIRED_ORGANIZATIONS': 'nuxeo'
        })

        self.assertListEqual(['mguillaume', 'tmartins'], review_service.get_owners(event))

        [patcher.stop() for patcher in patchers]

    def test_review_pull_request(self):
        with GithubHookHandlerTest.payload_file('github_issue_comment') as payload:
            payload_body = self.get_json_body_from_payload(payload)

        event = IssueCommentEvent(None, None, payload_body, True)
        handler = services.get(GithubReviewCommentHandler)  # type: GithubReviewCommentHandler

        services.get(Config).set_request_environ({
            Config.ENV_PREFIX + 'GITHUBREVIEW_ACTIVE': True
        })

        self.mocks.commit.get_statuses.return_value.reversed = [CommitStatus(None, None, {
            "context": "code-review/nuxeo"
        }, True)]
        self.mocks.organization.get_repo.return_value.get_pull.return_value.get_commits.return_value.reversed = \
            [self.mocks.commit]
        self.mocks.organization.get_repo.return_value.get_pull.return_value.get_issue_comments.return_value = \
            [event.comment]

        handler._do_handle(payload_body)

        self.mocks.commit.create_status.assert_called_once()

        payload_body['comment']['body'] = u"👍 "
        self.mocks.commit.create_status.reset_mock()
        handler._do_handle(payload_body)

        self.mocks.commit.create_status.assert_called_once()
