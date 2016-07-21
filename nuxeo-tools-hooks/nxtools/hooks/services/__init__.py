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

from abc import ABCMeta, abstractmethod
from nxtools import services
from nxtools.hooks.services.config import Config


class AbstractService(object):
    __metaclass__ = ABCMeta

    def config(self, key, default=None):
        return services.get(Config).get(Config.get_section(self), key, default)


class BootableService(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def boot(self, app):
        """ :type app: nxtools.hooks.app.ToolsHooksApp """
        pass
