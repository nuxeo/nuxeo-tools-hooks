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

import json
import logging

from flask import request
from flask.blueprints import Blueprint
from flask_cors.extension import CORS
from nxtools import ServiceContainer, services
from nxtools.hooks.endpoints import AbstractEndpoint
from nxtools.hooks.services import BootableService
from nxtools.hooks.services.csrf import CSRFService
from nxtools.hooks.services.github_service import GithubService
from nxtools.hooks.services.jwt_service import JwtService
from nxtools.hooks.services.oauth_service import OAuthService

log = logging.getLogger(__name__)


@ServiceContainer.service
class ApiEndpoint(AbstractEndpoint, BootableService):

    __blueprint = Blueprint('api', __name__)

    def boot(self, app):
        """ :type app: nxtools.hooks.app.ToolsHooksApp """

        CORS(ApiEndpoint.blueprint(), **services.get(ApiEndpoint).get_cors_config())
        app.flask.register_blueprint(ApiEndpoint.blueprint(), url_prefix="/api")

    @staticmethod
    def blueprint():
        return ApiEndpoint.__blueprint

    @staticmethod
    @__blueprint.route('/services')
    @OAuthService.secured
    def services():
        try:
            return json.dumps([t.__module__ + "." + t.__name__ for t, n, v in services.list(object)])
        except Exception, e:
            log.warn('services: Could not list services: %s', e)
            return 'KO', 500

    @staticmethod
    @__blueprint.route('/validate/<code>')
    @JwtService.update_jwt
    def validate(code):
        try:
            return services.get(OAuthService).validate(code)
        except Exception, e:
            log.warn('validate: Could not validate OAuth code: %s', e)
            return 'KO', 500

    @staticmethod
    @__blueprint.route('/me')
    @OAuthService.secured
    def me():
        try:
            if services.get(OAuthService).authenticated:
                return 'OK'
            else:
                return 'KO', 401
        except Exception, e:
            log.warn('me: Could not check for authentication: %s', e)
            return 'KO', 500

    @staticmethod
    @__blueprint.route('/pull_requests/sync', methods=['POST'])
    @CSRFService.secured
    @OAuthService.secured
    def sync_pull_requests():
        try:
            services.get(GithubService).sync_pull_requests()
            return 'OK'
        except Exception, e:
            log.warn('sync_pull_requests: Could not sync pull requests: %s', e)
            return 'KO', 500

    @staticmethod
    @__blueprint.route('/pull_requests')
    @OAuthService.secured
    def list_pull_requests():
        try:
            return json.dumps(services.get(GithubService).list_pull_requests())
        except Exception, e:
            log.warn('list_pull_requests: Could not list pull requests: %s', e)
            return 'KO', 500

    @staticmethod
    @__blueprint.route('/github/<organisation>/<repository>/webhooks', methods=['POST'])
    @CSRFService.secured
    @OAuthService.secured
    def setup_webhooks(organisation, repository):
        try:
            data = json.loads(request.data)
            if 'config' in data:
                services.get(GithubService).setup_webhooks(organisation, repository, data['config'])
                return 'OK', 200
            else:
                return 'KO', 400
        except Exception, e:
            log.warn('setup_webhooks: Could not setup %s/%s webhooks: %s', organisation, repository, e)
            return 'KO', 500

    def get_cors_config(self):
        return {k.replace("cors_", ""): v for k, v in self.config.items(self.config_section, {
            "cors_origins": "*",
            "cors_supports_credentials": True
        }).iteritems() if k.startswith("cors_")}
