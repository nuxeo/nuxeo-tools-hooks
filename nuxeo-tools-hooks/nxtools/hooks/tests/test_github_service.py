from github.PullRequest import PullRequest
from nxtools import services
from nxtools.hooks.entities.db_entities import StoredPullRequest
from nxtools.hooks.services.config import Config
from nxtools.hooks.services.database import DatabaseService
from nxtools.hooks.services.github_service import GithubService
from nxtools.hooks.tests import HooksTestCase


class GithubServiceTest(HooksTestCase):

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

        self.assertEqual(0, len(StoredPullRequest.objects))

        self.mocks.repository.name = 'mock_repository'
        self.mocks.repository.get_pulls.return_value = [PullRequest(None, {}, pull_request, True)]
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
