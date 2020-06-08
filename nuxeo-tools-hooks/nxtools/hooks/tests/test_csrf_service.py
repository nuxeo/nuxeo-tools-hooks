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

import flask
from flask.helpers import make_response
from mock.mock import patch
from nxtools.hooks.services.csrf import CSRFService
from nxtools.hooks.tests import HooksTestCase


class CSRFServiceTest(HooksTestCase):

    @property
    def app(self):
        return flask.Flask(__name__)

    def testEncode(self):
        service = CSRFService()
        token = service.get_random_string()
        encoded = service.encode_token(token)

        self.assertEqual(token, service.decode_token(encoded))

    def testValidate(self):
        service = CSRFService()
        token = service.get_random_string()
        encoded = service.encode_token(token)
        new_token = service.get_random_string()
        new_encoded = service.encode_token(new_token)

        self.mocks.jwt_get.return_value = token
        self.mocks.jwt_encode.return_value = ''
        self.mocks.get_random_string.return_value = new_token
        self.mocks.encode_token.return_value = new_encoded

        with self.app.test_request_context():
            self.assertFalse(service.validate())

        with self.app.test_request_context(headers={CSRFService.CSRF_HEADER: encoded}), \
                patch('nxtools.hooks.services.jwt_service.JwtService.get', self.mocks.jwt_get), \
                patch('nxtools.hooks.services.jwt_service.JwtService.set', self.mocks.jwt_set), \
                patch('nxtools.hooks.services.jwt_service.JwtService.encode', self.mocks.jwt_encode), \
                patch('nxtools.hooks.services.csrf.CSRFService.get_random_string', self.mocks.get_random_string), \
                patch('nxtools.hooks.services.csrf.CSRFService.encode_token', self.mocks.encode_token):

            def fake_controller():
                return make_response()

            self.assertTrue(service.validate())
            self.assertTrue(self.mocks.jwt_set.called)

            response = self.app.process_response(fake_controller())

            for header in response.headers:
                key, value = header
                if CSRFService.CSRF_HEADER == key and new_encoded == value:
                    return

            self.fail('Cannot find %s in %s' % (new_encoded, response.headers))
