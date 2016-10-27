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
from mock.mock import patch
from nxtools import services
from nxtools.hooks.endpoints.webhook.github_handlers.jenkins_trigger import GithubJenkinsTriggerHandler
from nxtools.hooks.endpoints.webhook.github_hook import GithubHook
from nxtools.hooks.services.config import Config
from nxtools.hooks.services.jenkins import JenkinsService
from nxtools.hooks.tests.webhooks.github_handlers import GithubHookHandlerTest


class GithubJenkinsTriggerHandlerTest(GithubHookHandlerTest):

    def test_jenkins_trigger(self):

        base_url = 'http://void.null'
        services.get(Config).set_request_environ({
            Config.ENV_PREFIX + 'JENKINS_DEFAULT_USERNAME': 'some_username',
            Config.ENV_PREFIX + 'JENKINS_DEFAULT_TOKEN': 'some_token',
            Config.ENV_PREFIX + 'JENKINS_INSTANCE_QATEST_URL': base_url,
            Config.ENV_PREFIX + 'GITHUBJENKINSTRIGGERHANDLER_INSTANCES': 'qatest'
        })

        with GithubHookHandlerTest.payload_file('github_push') as payload, patch('nxtools.hooks.services.jenkins.Jenkins') as mock:
            mock.return_value.base_server_url.return_value = base_url

            handler = GithubJenkinsTriggerHandler()
            self.assertTupleEqual((200, 'OK'), handler.handle(payload))

            mock.return_value.requester.post_and_confirm_status.\
                assert_called_once_with(base_url + handler.DEFAULT_GITHUB_URL,
                                        data=payload,
                                        headers={'Content-Type': 'application/json', GithubHook.payloadHeader: 'push'})
