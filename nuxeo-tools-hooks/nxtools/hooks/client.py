#!/usr/bin/env python
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
import os
import logging

import json
import requests
import sys

from urlparse import urljoin


logging.basicConfig(level=logging.INFO)


class CaptainHooksClient:

    CAPTAIN_HOOKS_URL = os.getenv('CAPTAIN_HOOKS_URL', 'http://localhost:5000')
    COOKIE_JWT = 'access_token'
    HEADER_CSRF = 'X-CSRFToken'

    def __init__(self, github_token):
        login_reponse = requests.get(
            urljoin(self.CAPTAIN_HOOKS_URL, '/api/me'),
            headers={'X-GITHUB-ACCESS-TOKEN': github_token})

        if 401 == login_reponse.status_code:
            logging.critical('Could not log on Captain Hooks with the given credentials')
            sys.exit(1)

        self.jwt = login_reponse.cookies[self.COOKIE_JWT]
        self.csrf = login_reponse.headers[self.HEADER_CSRF]

    def setup_webhooks(self, organization, repository, hooks_config):
        response = requests.post(
            urljoin(self.CAPTAIN_HOOKS_URL, '/api/github/%s/%s/webhooks' % (organization, repository)),
            cookies={self.COOKIE_JWT: self.jwt},
            headers={self.HEADER_CSRF: self.csrf},
            data=json.dumps(hooks_config))

        test=True
