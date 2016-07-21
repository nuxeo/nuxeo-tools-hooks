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

import random
import string
import logging

from flask.ctx import after_this_request
from flask.globals import request
from functools import wraps
from nxtools import ServiceContainer, services
from nxtools.hooks.services import AbstractService
from nxtools.hooks.services.jwt_service import JwtService

log = logging.getLogger(__name__)


@ServiceContainer.service
class CSRFService(AbstractService):

    CSRF_HEADER = 'X-CSRFToken'
    CSRF_CHARACTERS = string.ascii_letters + string.digits
    CSRF_SECRET_LENGTH = 32

    @staticmethod
    def secured(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            if services.get(CSRFService).validate():
                return fn(*args, **kwargs)
            else:
                return 'Unauthorized', 403
        return decorated

    '''
    From django.utils.crypto
    '''
    def get_random_string(self):
        rnd = random.SystemRandom()
        return ''.join(rnd.choice(CSRFService.CSRF_CHARACTERS) for i in range(CSRFService.CSRF_SECRET_LENGTH))

    '''
    From django.utils.crypto
    '''
    def encode_token(self, token):
        chars = CSRFService.CSRF_CHARACTERS
        salt = self.get_random_string()

        pairs = zip((chars.index(x) for x in token), (chars.index(x) for x in salt))
        cipher = ''.join(chars[(x + y) % len(chars)] for x, y in pairs)

        return salt + cipher

    '''
    From django.utils.crypto
    '''
    def decode_token(self, token):
        salt = token[:CSRFService.CSRF_SECRET_LENGTH]
        token = token[CSRFService.CSRF_SECRET_LENGTH:]
        chars = CSRFService.CSRF_CHARACTERS

        pairs = zip((chars.index(x) for x in token), (chars.index(x) for x in salt))
        secret = ''.join(chars[x - y] for x, y in pairs)
        return secret

    @JwtService.update_jwt
    def update(self):
        token = self.get_random_string()
        encoded = self.encode_token(token)
        log.debug('New token: %s encoded as %s', token, encoded)

        services.get(JwtService).set('csrf', token)

        @after_this_request
        def post_request(response):
            response.headers[CSRFService.CSRF_HEADER] = encoded
            return response

    def validate(self):
        token = services.get(JwtService).get('csrf')
        if CSRFService.CSRF_HEADER in request.headers and token is not None:
            if token == self.decode_token(request.headers.get(CSRFService.CSRF_HEADER)):
                log.debug('CSRF submitted: %s', request.headers.get(CSRFService.CSRF_HEADER))
                self.update()
                return True
            else:
                log.warn('Wrong CSRF submitted: %s', request.headers.get(CSRFService.CSRF_HEADER))
                return False
        else:
            log.warn('No CSRF submitted')
            return False
