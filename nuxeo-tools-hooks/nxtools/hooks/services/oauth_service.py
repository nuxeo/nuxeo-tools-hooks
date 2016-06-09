import datetime
import logging

from functools import wraps

import jwt

from flask.blueprints import Blueprint
from flask.globals import request
from flask.helpers import make_response
from flask.wrappers import Response
from jwt.exceptions import DecodeError
from nxtools import ServiceContainer, services
from nxtools.hooks.services.config import Config
from requests_oauthlib.oauth2_session import OAuth2Session

log = logging.getLogger(__name__)


@ServiceContainer.service
class OAuthService(object):

    __blueprint = Blueprint('oauth', __name__)

    CONFIG_SECTION = 'OAuthService'

    def get_cors_config(self):
        return {k.replace("cors_", ""): v for k, v in services.get(Config).items(OAuthService.CONFIG_SECTION, {
            "cors_origins": "*",
            "cors_supports_credentials": True
        }).iteritems() if k.startswith("cors_")}

    @staticmethod
    def secured(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            if services.get(OAuthService).authenticated:
                return fn(*args, **kwargs)
            else:
                return 'Unauthorized', 401
        return decorated

    @property
    def authenticated(self):
        if 'access_token' in request.cookies:
            try:
                access_token = jwt.decode(
                    request.cookies['access_token'],
                    self.config('jwt_secret', 'secret'),
                    audience='dashboard.qa.nuxeo.org',
                    issuer='hooks.nuxeo.org')
                return True
            except DecodeError:
                log.warn('Invalid JWT: %s', request.cookies['access_token'])
        return False

    def config(self, key, default=None):
        return services.get(Config).get(OAuthService.CONFIG_SECTION, key, default)

    def validate(self, code):
        github = OAuth2Session(self.config('consumer_key'))
        github_token = github.fetch_token('https://github.com/login/oauth/access_token',
                                          client_secret=self.config('consumer_secret'),
                                          code=code)

        response = make_response()  # type: Response
        access_token = jwt.encode({
            'sub': 'hooks-oauth',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(self.config('jwt_expires', 3600)),
            'nbf': datetime.datetime.utcnow(),
            'iss': 'hooks.nuxeo.org',
            'aud': 'dashboard.qa.nuxeo.org',
            'iat': datetime.datetime.utcnow(),
            'gat': github_token['access_token']  # Github Access Token
        },
            self.config('jwt_secret', 'secret'),
            algorithm=self.config('jwt_algorithm', 'HS256'))
        log.info('Generated new JWT: %s', access_token)
        response.set_cookie('access_token', access_token, httponly=True)

        return response
