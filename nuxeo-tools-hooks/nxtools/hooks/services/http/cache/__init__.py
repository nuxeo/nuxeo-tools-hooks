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

from abc import ABCMeta, abstractmethod

from geventhttpclient.httplib import HTTPConnection, HTTPSConnection
from nxtools import services
from nxtools.hooks.services.http import HTTPService

log = logging.getLogger(__name__)


class HTTPCache(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, method, url, body=None, headers={}, default=None):
        pass

    @abstractmethod
    def set(self, method, url, response, body=None, headers={}):
        pass

    @abstractmethod
    def has(self, method, url, body=None, headers={}):
        pass


class CachingHTTPMixin(object):

    HEADER_ETAG_REQUEST = 'If-None-Match'
    HEADER_ETAG_RESPONSE = 'ETag'

    HEADER_LAST_MODIFIED_REQUEST = 'If-Modified-Since'

    def __init__(self, cls):
        self._cache = services.get(HTTPService).cache  # type: HTTPCache
        self._cached_key = None
        self._cached_response = None
        self._connection_class = cls

    def request(self, method, url, body=None, headers={}):
        cache = services.get(HTTPService).cache
        self._cached_key = (method, url, body, headers)

        if cache.has(*self._cached_key):
            self._cached_response = cache.get(*self._cached_key)

            if CachingHTTPMixin.HEADER_ETAG_REQUEST.lower() not in [h.lower() for h in headers] \
                    or CachingHTTPMixin.HEADER_LAST_MODIFIED_REQUEST.lower() not in [h.lower() for h in headers]:
                headers[CachingHTTPMixin.HEADER_ETAG_REQUEST] = \
                    self._cached_response[CachingHTTPMixin.HEADER_ETAG_RESPONSE]
        else:
            self._cached_response = None

        self._connection_class.request(self, method, url, body, headers)

    def getresponse(self, buffering=False):
        cache = services.get(HTTPService).cache

        response = self._connection_class.getresponse(self, buffering)
        if self._cached_response is not None and 304 == response.status_code:
            log.debug('Cache hit: %s', self._cached_key)
            return self._cached_response
        else:
            log.debug('Cache miss: %s', self._cached_key)
            method, url, body, headers = self._cached_key
            cachable_response = services.get(HTTPService).response_class(response)
            cache.set(method, url, cachable_response, body, headers)
            return cachable_response


class CachingHTTPConnection(HTTPConnection, CachingHTTPMixin):

    def __init__(self, *args, **kw):
        HTTPConnection.__init__(self, *args, **kw)
        CachingHTTPMixin.__init__(self, HTTPConnection)

    def request(self, method, url, body=None, headers={}):
        CachingHTTPMixin.request(self, method, url, body, headers)

    def getresponse(self, buffering=False):
        return CachingHTTPMixin.getresponse(self, buffering)


class CachingHTTPSConnection(HTTPSConnection, CachingHTTPMixin):

    def __init__(self, *args, **kw):
        HTTPSConnection.__init__(self, *args, **kw)
        CachingHTTPMixin.__init__(self, HTTPSConnection)

    def request(self, method, url, body=None, headers={}):
        CachingHTTPMixin.request(self, method, url, body, headers)

    def getresponse(self, buffering=False):
        return CachingHTTPMixin.getresponse(self, buffering)


class CachableHTTPResponse(object):
    __metaclass__ = ABCMeta

    def __init__(self, wrappee):
        object.__setattr__(self, "_wrappee", wrappee)
        object.__setattr__(self, "_cached_body", None)

    def __getattr__(self, name):
        return getattr(self._wrappee, name)

    def __setattr__(self, name, value):
        if hasattr(self, name):
            object.__setattr__(self, name, value)
        else:
            object.__setattr__(self._wrappee, name, value)

    def __getitem__(self, item):
        return self._wrappee[item]

    def __eq__(self, other):
        return self._wrappee == other

