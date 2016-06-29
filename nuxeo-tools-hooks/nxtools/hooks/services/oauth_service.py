import logging

from functools import wraps
from flask.blueprints import Blueprint
from flask.globals import request
from nxtools import ServiceContainer, services
from nxtools.hooks.services.config import Config
from nxtools.hooks.services.jwt_service import JwtService
from requests_oauthlib.oauth2_session import OAuth2Session

log = logging.getLogger(__name__)


@ServiceContainer.service
class OAuthService(object):

    __blueprint = Blueprint('oauth', __name__)

    CONFIG_SECTION = 'OAuthService'

    @staticmethod
    def secured(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            if services.get(OAuthService).authenticated:
                log.debug(' * Authorized request to ' + request.url)
                return fn(*args, **kwargs)
            else:
                log.warn(' * Unauthorized request to ' + request.url)
                return 'Unauthorized', 401
        return decorated

    @property
    def authenticated(self):
        return services.get(JwtService).has_jwt()

    def config(self, key, default=None):
        return services.get(Config).get(OAuthService.CONFIG_SECTION, key, default)

    def validate(self, code):
        github = OAuth2Session(self.config('consumer_key'))
        github_token = github.fetch_token('https://github.com/login/oauth/access_token',
                                          client_secret=self.config('consumer_secret'),
                                          code=code)

        services.get(JwtService).set('gat', github_token['access_token'])  # Github Access Token
        return 'OK'
