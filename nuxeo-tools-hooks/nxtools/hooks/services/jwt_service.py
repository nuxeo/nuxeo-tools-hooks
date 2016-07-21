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

import datetime

from functools import wraps

import jwt
import logging

from flask.ctx import after_this_request
from flask.globals import request, g
from jwt.exceptions import DecodeError
from nxtools import ServiceContainer, services
from nxtools.hooks.services import AbstractService

log = logging.getLogger(__name__)


@ServiceContainer.service
class JwtService(AbstractService):

    def decode(self, create=False):
        if 'decoded_jwt' not in g:
            if 'access_token' in request.cookies:
                try:
                    g.decoded_jwt = jwt.decode(
                        request.cookies['access_token'],
                        self.config('jwt_secret', 'secret'),
                        audience='dashboard.qa.nuxeo.org',
                        issuer='hooks.nuxeo.org')

                    return g.get('decoded_jwt')
                except DecodeError, e:
                    log.warn('Invalid JWT: %s, %s', e, request.cookies['access_token'])
            if create:
                g.decoded_jwt = {
                    'sub': 'hooks-oauth',
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(self.config('jwt_expires', 3600)),
                    'nbf': datetime.datetime.utcnow(),
                    'iss': 'hooks.nuxeo.org',
                    'aud': 'dashboard.qa.nuxeo.org',
                    'iat': datetime.datetime.utcnow(),
                }

        return g.get('decoded_jwt')

    def encode(self):
        return jwt.encode(g.get('decoded_jwt'),
                          self.config('jwt_secret', 'secret'),
                          algorithm=self.config('jwt_algorithm', 'HS256'))

    def has_jwt(self):
        return self.decode() is not None

    def get(self, parameter):
        jwt = self.decode() if self.has_jwt() else {}
        return jwt.get(parameter, None)

    def set(self, key, value):
        decoded = self.decode(True)
        decoded[key] = value

        return self

    @staticmethod
    def update_jwt(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            @after_this_request
            def post_request(response):
                access_token = services.get(JwtService).encode()
                log.info('Generated new JWT: %s', access_token)
                response.set_cookie('access_token', access_token, httponly=True)

                return response

            return fn(*args, **kwargs)
        return decorated
