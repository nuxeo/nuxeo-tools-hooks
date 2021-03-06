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

from geventhttpclient.httplib import HTTPResponse
from mock.mock import patch
from nxtools.hooks.services.http.cache import CachingHTTPConnection, CachingHTTPMixin
from nxtools.hooks.tests import HooksTestCase


class HTTPTest(HooksTestCase):

    def setUp(self):
        super(HTTPTest, self).setUp()

        patchers = [
            patch("gevent.socket.create_connection", self.mocks.socket_connect),
            patch("httplib.HTTPConnection.request", self.mocks.http_request),
            patch("httplib.HTTPConnection.getresponse", self.mocks.http_getresponse),
            patch("geventhttpclient.httplib.HTTPResponse.read", self.mocks.httpresponse_read),
            patch("geventhttpclient.response.HTTPSocketResponse._read_headers"),
        ]

        [patcher.start() for patcher in patchers]
        [self.addCleanup(patcher.stop) for patcher in patchers]

    def test_http_caching(self):
        cnx = CachingHTTPConnection('mocked.lan', 80)

        cnx.connect()
        cnx.request('GET', '/test', 'Lorem Ipsum', {'X-HEADER': 'value'})

        fake_response = HTTPResponse(None)
        headers = fake_response.info()
        headers[CachingHTTPMixin.HEADER_ETAG_RESPONSE] = '644b5b0155e6404a9cc4bd9d8b1ae730'
        self.mocks.http_getresponse.return_value = fake_response
        self.mocks.httpresponse_read.return_value = "Mocked Response"

        response = cnx.getresponse()

        cnx.request('GET', '/test', 'Lorem Ipsum', {'X-HEADER': 'value'})
        empty_response = HTTPResponse(None)
        empty_response.get_code = lambda: 304
        self.mocks.http_getresponse.return_value = empty_response

        response2 = cnx.getresponse()
        response2.read()

        self.assertTrue(self.mocks.socket_connect.called)
        self.assertEqual(2, self.mocks.http_request.call_count)
        self.assertEqual(2, self.mocks.http_getresponse.call_count)
        self.assertEqual(response, fake_response)
        self.assertEqual(fake_response, response2)
        self.assertEqual(response.read(), response2.read())

    def test_http_noetag(self):
        cnx = CachingHTTPConnection('mocked.lan', 80)

        cnx.connect()
        cnx.request('GET', '/test', 'Lorem Ipsum', {'X-HEADER': 'value'})

        self.mocks.http_getresponse.return_value = HTTPResponse(None)
        self.mocks.httpresponse_read.return_value = "Mocked Response"

        response1 = cnx.getresponse()

        cnx.request('GET', '/test', 'Lorem Ipsum', {'X-HEADER': 'value'})
        self.mocks.http_getresponse.return_value = HTTPResponse(None)
        self.mocks.httpresponse_read.return_value = "Mocked Response"

        response2 = cnx.getresponse()
        self.assertNotEquals(response1, response2)
