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
import logging

from nxtools import ServiceContainer
from nxtools.hooks.endpoints.webhook.github_handlers import AbstractGithubHandler
from nxtools.hooks.endpoints.webhook.github_hook import GithubHook

log = logging.getLogger(__name__)


@ServiceContainer.service
class GithubPingHandler(AbstractGithubHandler):

    def can_handle(self, headers, body):
        return "ping" == headers[GithubHook.payloadHeader]

    def _do_handle(self, payload_body):
        log.info('GithubPingHandler.handle')
        return 200, 'PONG'
