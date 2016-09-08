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

from flask.app import Flask
from mock.mock import patch
from nxtools import services
from nxtools.hooks.endpoints.webhook import WebHookEndpoint, NoSuchHookException
from nxtools.hooks.endpoints.webhook.github_hook import GithubHook, UnhandledGithubEvent, InvalidPayloadException
from nxtools.hooks.tests.webhooks import WebHooksTestCase


class WebhooksTest(WebHooksTestCase):

    def setUp(self):
        super(WebhooksTest, self).setUp()
        self.flask = Flask(__name__)

    def test_routing(self):
        endpoint = services.get(WebHookEndpoint)
        """:type : WebHookEndpoint"""

        with open('nxtools/hooks/tests/resources/github_handlers/github_pullrequest_open.headers.json') \
                as headers_file, \
                open('nxtools/hooks/tests/resources/github_handlers/github_pullrequest_open.json') as body_file, \
                self.flask.test_request_context("/", headers=json.load(headers_file), data=body_file.read()), \
                patch("nxtools.hooks.endpoints.webhook.github_hook.GithubHook.can_handle", self.mocks.can_handle),\
                patch("nxtools.hooks.endpoints.webhook.github_hook.GithubHook.handle", self.mocks.handle):

            self.mocks.can_handle.return_value = False

            with self.assertRaises(NoSuchHookException):
                endpoint.route()
            self.mocks.can_handle.assert_called_once()
            self.mocks.handle.assert_not_called()

            self.mocks.can_handle.return_value = True
            endpoint.route()
            self.assertEqual(2, self.mocks.can_handle.call_count)
            self.mocks.handle.assert_called_once()

    def test_github(self):
        hook = GithubHook()
        with self.assertRaises(UnhandledGithubEvent):
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
