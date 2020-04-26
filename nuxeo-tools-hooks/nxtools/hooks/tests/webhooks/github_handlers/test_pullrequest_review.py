# -*- coding: utf-8 -*-
"""
(C) Copyright 2016-2019 Nuxeo SA (http://nuxeo.com/) and contributors.

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
    jcarsique
"""
import json

from nxtools.hooks.entities.github_entities import PullRequestEvent
from nxtools.hooks.tests.webhooks.github_handlers import GithubHookHandlerTest

class GithubReviewPullRequestHandlerTest(GithubHookHandlerTest):

    def test_open_pull_request(self):
        with GithubHookHandlerTest.payload_file('github_pullrequest_open') as payload:
            body = self.get_json_body_from_payload(payload)
        event = PullRequestEvent(None, None, body, True)
        self.assertEqual(body["action"], event.action)
        self.assertEqual(body["number"], event.number)
        self.assertEqual(body["pull_request"]["head"]["ref"], event.pull_request.head.ref)
        self.assertEqual(body["pull_request"]["head"]["sha"], event.pull_request.head.sha)
        self.assertEqual(body["repository"]["name"], event.repository.name)
