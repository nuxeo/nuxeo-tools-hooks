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
from mock.mock import patch, call, Mock

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

    def test_hooks_setup(self):
        github = services.get(GithubService)  # type: GithubService

        hook_name = 'new_hook'
        delete_hook_name = 'delete_hook'
        del_urlhook_name = 'url_hook'
        del_urlhook_url = 'http://void.null/delete'
        update_hook_name = 'update_hook'

        hook_config = {
            'url': 'http://void.null/hook',
            'content_type': 'json'
        }

        update_hook_config = {
            'url': 'http://void.null/new',
            'content_type': 'json'
        }

        hook_events = ["push"]

        setup_config = {
            'present': [
                {
                    'name': hook_name,
                    'config': hook_config,
                    'events': hook_events,
                    'active': True
                },
                {
                    'name': update_hook_name,
                    'config': update_hook_config,
                    'events': hook_events,
                    'active': True
                }
            ],
            'absent': [delete_hook_name, {'url': del_urlhook_url}]
        }

        self.mocks.organization.get_repo.return_value = self.mocks.repository
        self.mocks.hook.name = delete_hook_name
        self.mocks.url_hook.name = del_urlhook_name
        self.mocks.url_hook.url = del_urlhook_url
        self.mocks.update_hook.name = update_hook_name
        self.mocks.update_hook.url = 'http://void.null/old'
        self.mocks.repository.get_hooks.return_value = [self.mocks.hook, self.mocks.url_hook, self.mocks.update_hook]

        github.setup_webhooks('nuxeo', 'repository', setup_config)

        self.mocks.repository.create_hook.assert_called_once_with(hook_name, hook_config, hook_events, True)
        self.mocks.update_hook.edit.assert_called_once_with(
            update_hook_name, update_hook_config, hook_events, active=True)
        self.assertTrue(self.mocks.hook.delete.called)
        self.assertTrue(self.mocks.url_hook.delete.called)
