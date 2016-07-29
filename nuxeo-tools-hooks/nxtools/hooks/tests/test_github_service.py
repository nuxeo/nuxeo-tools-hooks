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

from github.PullRequest import PullRequest
from nxtools import services
from nxtools.hooks.entities.db_entities import StoredPullRequest
from nxtools.hooks.services.config import Config
from nxtools.hooks.services.database import DatabaseService
from nxtools.hooks.services.github_service import GithubService
from nxtools.hooks.tests import HooksTestCase


class GithubServiceTest(HooksTestCase):

    class MockedPullRequestList(list):

        @property
        def totalCount(self):
            return self.__len__()

    def setUp(self):
        super(GithubServiceTest, self).setUp()

        services.get(DatabaseService).connect()

    def tearDown(self):
        super(GithubServiceTest, self).tearDown()

        StoredPullRequest.drop_collection()

    def test_sync_github_pull_requests(self):
        github = services.get(GithubService)  # type: GithubService

        pull_request = {
            'number': 42,
            'head': {
                'sha': '123456',
                'ref': 'master'
            }
        }

        pull_requests_list = GithubServiceTest.MockedPullRequestList()
        pull_requests_list.append(PullRequest(None, {}, pull_request, True))

        self.assertEqual(0, len(StoredPullRequest.objects))

        self.mocks.repository.name = 'mock_repository'
        self.mocks.repository.get_pulls.return_value = pull_requests_list
        self.mocks.repository.organization = self.mocks.organization
        self.mocks.organization.get_repos.return_value = [self.mocks.repository]
        services.get(Config).set_request_environ({
            Config.ENV_PREFIX + 'GITHUB_SYNC_PULLREQUESTS_ORGANIZATIONS': 'nuxeo,void'
        })

        github.sync_pull_requests()

        self.assertEqual(1, len(StoredPullRequest.objects))
        stored_pull_request = StoredPullRequest.objects[0]  # type: StoredPullRequest

        self.assertEqual(self.mocks.organization.login, stored_pull_request.organization)
        self.assertEqual(self.mocks.repository.name, stored_pull_request.repository)
        self.assertDictEqual(pull_request, {
            'number': stored_pull_request.pull_number,
            'head': {
                'sha': stored_pull_request.head_commit,
                'ref': stored_pull_request.branch
            }
        })

        new_pull_request = pull_request.copy()
        new_pull_request['number'] = 43
        pull_request['state'] = "closed"

        pull_requests_list = GithubServiceTest.MockedPullRequestList()
        pull_requests_list.append(PullRequest(None, {}, new_pull_request, True))

        self.mocks.repository.get_pulls.return_value = pull_requests_list
        self.mocks.repository.get_pull.return_value = PullRequest(None, {}, pull_request, True)

        github.sync_pull_requests()

        self.assertEqual(1, len(StoredPullRequest.objects))

        stored_pull_request = StoredPullRequest.objects[0]  # type: StoredPullRequest
        self.assertDictEqual(new_pull_request, {
            'number': stored_pull_request.pull_number,
            'head': {
                'sha': stored_pull_request.head_commit,
                'ref': stored_pull_request.branch
            }
        })
