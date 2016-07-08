from geventhttpclient.response import HTTPResponse
from mock.mock import patch
from nxtools.hooks.services.http import CachingHTTPConnection
from nxtools.hooks.tests import HooksTestCase


class HTTPTest(HooksTestCase):

    def setUp(self):
        super(HTTPTest, self).setUp()

        self.mocks.http_getresponse.return_value = HTTPResponse('test')

        patchers = [
            patch("gevent.socket.create_connection", self.mocks.socket_connect),
            patch("httplib.HTTPConnection.request", self.mocks.http_request),
            patch("httplib.HTTPConnection.getresponse", self.mocks.http_getresponse),
        ]

        [patcher.start() for patcher in patchers]
        [self.addCleanup(patcher.stop) for patcher in patchers]

    def test_http_caching(self):
        cnx = CachingHTTPConnection('mocked.lan', 80)

        cnx.connect()
        cnx.request('GET', '/test', 'Lorem Ipsum', {'X-HEADER': 'value'})
        response = cnx.getresponse()

        cnx.request('GET', '/test', 'Lorem Ipsum', {'X-HEADER': 'value'})
        response2 = cnx.getresponse()

        self.assertTrue(self.mocks.socket_connect.called)
        self.assertEqual(1, self.mocks.http_request.call_count)
        self.assertEqual(1, self.mocks.http_getresponse.call_count)
        self.assertEqual(response, response2)
