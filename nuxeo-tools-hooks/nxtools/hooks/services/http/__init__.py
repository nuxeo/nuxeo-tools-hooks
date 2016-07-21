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

import sys

from importlib import import_module

from nxtools import ServiceContainer
from nxtools.hooks.services import AbstractService


@ServiceContainer.service
class HTTPService(AbstractService):

    def __init__(self):
        cache_kls = self.config("cache_class", "nxtools.hooks.services.http.cache.memory.MemoryHTTPCache")
        resp_kls = self.config("response_class", "nxtools.hooks.services.http.cache.memory.MemoryCachableHTTPResponse")

        cache_pkg = cache_kls[:cache_kls.rfind('.')]
        response_pkg = resp_kls[:resp_kls.rfind('.')]

        [import_module(pkg) for pkg in [cache_pkg, response_pkg] if pkg not in sys.modules.items()]

        self._cache = getattr(sys.modules[cache_pkg], cache_kls[cache_kls.rfind('.')+1:])()
        self._response_class = getattr(sys.modules[response_pkg], resp_kls[resp_kls.rfind('.')+1:])

    @property
    def cache(self):
        return self._cache

    @property
    def response_class(self):
        return self._response_class
