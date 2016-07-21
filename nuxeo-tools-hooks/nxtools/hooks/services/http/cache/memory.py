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

import hashlib

from nxtools.hooks.services.http.cache import CachableHTTPResponse, HTTPCache


class MemoryCachableHTTPResponse(CachableHTTPResponse):

    def read(self, amt=None):
        if self._cached_body is None:
            self._cached_body = self._wrappee.read(amt)
        return self._cached_body


class MemoryHTTPCache(HTTPCache):

    def __init__(self):
        self._data = list()

    @staticmethod
    def build_key(method, url, body, headers):
        return method, url, len(body), hashlib.md5(body).hexdigest(), {key.lower(): value for key, value in headers.iteritems()}

    def get(self, method, url, body=None, headers={}, default=None):
        for key, value in self._data:
            if key == MemoryHTTPCache.build_key(method, url, body, headers):
                return value
        return default

    def set(self, method, url, response, body=None, headers={}):
        key = MemoryHTTPCache.build_key(method, url, body, headers)

        for index, item in enumerate(self._data):
            existing_key, value = item
            if key == existing_key:
                del self._data[index]
                break

        self._data.append((key, response))
        return self

    def has(self, method, url, body=None, headers={}):
        key = MemoryHTTPCache.build_key(method, url, body, headers)

        for existing_key, value in self._data:
            if key == existing_key:
                return True

        return False

