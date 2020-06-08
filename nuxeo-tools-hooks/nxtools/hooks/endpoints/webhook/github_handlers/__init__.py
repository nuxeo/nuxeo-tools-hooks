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

from abc import ABCMeta, abstractmethod
from nxtools import services
from nxtools.hooks.services.config import Config

log = logging.getLogger(__name__)


class AbstractGithubHandler(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.__config_section = type(self).__name__

    def handle(self, payload_body):
        if services.get(Config).getboolean(self.config_section, 'active', True):
            try:
                return self._do_handle(payload_body)
            except Exception, e:
                log.warn('Unhandled exception: %s', e.message, exc_info=True)
                return 500, "Unhandled exception"
        else:
            return 204, "Disabled"

    @abstractmethod
    def _do_handle(self, json_payload_body):
        pass

    @abstractmethod
    def can_handle(self, headers, body):
        pass

    @property
    def config_section(self):
        return self.__config_section

    def get_config(self, key, default=None):
        return services.get(Config).get(self.config_section, key, default)


class AbstractGithubJsonHandler(AbstractGithubHandler):
    __metaclass__ = ABCMeta

    def handle(self, payload_body):
        return AbstractGithubHandler.handle(self, json.loads(payload_body))

