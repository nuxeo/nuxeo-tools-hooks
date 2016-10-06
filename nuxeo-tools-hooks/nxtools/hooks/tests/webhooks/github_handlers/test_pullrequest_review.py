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

from github.CommitStatus import CommitStatus
from github.File import File
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

        self.mocks.organization.get_repo.return_value.html_url = 'http://void.null/'
        self.mocks.organization.get_repo.return_value.get_pull.return_value.id = 42
        self.mocks.organization.get_repo.return_value.get_pull.return_value.get_files.return_value = self.mocks.files

        deletions = review_service.parse_patch(self.mocks.files[1].patch)

        self.assertEqual(3, len(deletions))

        self.assertEqual(1408, len([l for l in blame if l == 'jcarsique']))
        self.assertEqual(105, len([l for l in blame if l == 'mguillaume']))
        self.assertEqual(59, len([l for l in blame if l == 'efge']))
        self.assertEqual(40, len([l for l in blame if l == 'atchertchian']))

        with patch('nxtools.hooks.endpoints.webhook.github_handlers.pullrequest_review.GithubReviewService.parse_patch',
                   return_value=deletions), patch(
            'nxtools.hooks.endpoints.webhook.github_handlers.pullrequest_review.GithubReviewService.parse_blame',
            return_value=blame), patch('nxtools.hooks.entities.github_entities.RepositoryWrapper.get_blame',
                                       return_value=None):

            self.assertListEqual(['jcarsique', 'efge', 'atchertchian'], review_service.get_owners(event))

    def test_review_pull_request(self):
        with GithubHookHandlerTest.payload_file('github_issue_comment') as payload:
            body = self.get_json_body_from_payload(payload)

        event = IssueCommentEvent(None, None, body, True)
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

        handler.handle(body)

        self.mocks.commit.create_status.assert_called_once()