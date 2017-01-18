# coding=UTF-8

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
import logging
import pkgutil
import sys
import types

from github.GithubException import UnknownObjectException
from io import StringIO
from nxtools import services, ServiceContainer
from nxtools.hooks.endpoints.webhook import AbstractWebHook, github_handlers
from nxtools.hooks.endpoints.webhook.github_handlers import AbstractGithubHandler
from nxtools.hooks.entities.github_entities import OrganizationWrapper
from nxtools.hooks.services.config import Config
from nxtools.hooks.services.github_service import NoSuchOrganizationException, GithubService

log = logging.getLogger(__name__)


class UnhandledGithubEvent(Exception):
    def __init__(self, headers, body):
        super(UnhandledGithubEvent, self).__init__("No proper handlers for github event '%s'" %
                                                   headers[GithubHook.payloadHeader])


class InvalidPayloadException(Exception):
    def __init__(self, previous):
        self.previous = previous

        super(InvalidPayloadException, self).__init__()


@ServiceContainer.service
class GithubHook(AbstractWebHook):

    eventSource = "Github"
    payloadHeader = "X-GitHub-Event"
    github_events = {}

    """:type : dict[str, list[AbstractGithubHandler]]"""

    def __init__(self):
        self.github = services.get(GithubService)

        loaded = [key for key, value in sys.modules.items()
                  if key.startswith(github_handlers.__name__) and isinstance(value, types.ModuleType)]

        for loader, module_name, is_pkg in pkgutil.iter_modules(github_handlers.__path__, github_handlers.__name__ + "."):
            if module_name not in loaded:
                loader.find_module(module_name).load_module(module_name)

    def can_handle(self, headers, body):
        return GithubHook.payloadHeader in headers

    @property
    def config(self):
        """
        :rtype: nxtools.hooks.services.config.Config
        """
        return services.get(Config)

    @property
    def handlers(self):
        return [handler for t, n, handler in services.list(AbstractGithubHandler)]

    def get_organization(self, name):
        """
        :rtype: nxtools.hooks.entities.github_entities.OrganizationWrapper
        """
        if name not in self._organizations:
            try:
                self._organizations[name] = OrganizationWrapper(self.github.get_organization(name))
            except UnknownObjectException:
                raise NoSuchOrganizationException(name)
        return self._organizations[name]

    def handle(self, headers, body):
        """
        @type headers : dict[str, str]
        @type body : str
        """

        if GithubHook.payloadHeader in headers:
            repository_name = None

            json_body = json.loads(body)
            if 'repository' in json_body and 'html_url' in json_body['repository']:
                repository_name = json_body['repository']['html_url']
            log.info('Got a payload %s - %s', repository_name, headers[GithubHook.payloadHeader])

            handlers = [handler for handler in self.handlers if handler.can_handle(headers, body)]

            if handlers:
                response = StringIO()
                status = 200

                for handler in handlers:
                    s, r = handler.handle(body)
                    response.writelines(unicode(r))
                    status = max(status, s)

                return response.getvalue(), status
            else:
                raise UnhandledGithubEvent(headers, body)
