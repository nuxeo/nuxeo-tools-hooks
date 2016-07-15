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

