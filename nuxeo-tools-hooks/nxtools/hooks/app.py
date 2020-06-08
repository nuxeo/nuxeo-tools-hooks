#!/usr/bin/env python
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
import os

from flask.app import Flask
from logging import FileHandler
from logging.config import fileConfig

from github.Requester import Requester
from nxtools import services
from nxtools.hooks import DEFAULTSECT
from nxtools.hooks.endpoints.api import ApiEndpoint
from nxtools.hooks.endpoints.webhook import WebHookEndpoint
from nxtools.hooks.services.config import Config
from nxtools.hooks.services.database import DatabaseService
from nxtools.hooks.services.http.cache import CachingHTTPConnection, CachingHTTPSConnection
from werkzeug.serving import run_simple


logging.basicConfig(level='INFO')
log = logging.getLogger(__name__)


class ToolsHooksApp(object):

    def __init__(self):
        self.__flask = None

    @property
    def config(self):
        return services.get(Config)

    @property
    def flask(self):
        """ :rtype: flask.app.Flaenvironsk"""
        return self.__flask

    def setup(self, request_environ=None):
        if request_environ is not None:
            self.config.set_request_environ({k: v for k, v in request_environ.iteritems()
                                             if k.startswith(Config.ENV_PREFIX)})

        log_file = self.config.get(DEFAULTSECT, "log_file")

        if log_file:
            if not os.path.exists(os.path.dirname(log_file)):
                os.makedirs(os.path.dirname(log_file))

            log.info(logging.root.handlers)
            del logging.root.handlers[:]
            logging.root.addHandler(FileHandler(log_file, 'a'))

        if self.config.get(DEFAULTSECT, "debug", False):
            log_level = logging.DEBUG
        else:
            log_level = self.config.get(DEFAULTSECT, 'log_level', 'INFO').upper()

        logging.root.setLevel(log_level)

        logging_config_file = self.config.get(DEFAULTSECT, "logging_config_file")
        if logging_config_file:
            fileConfig(logging_config_file, disable_existing_loggers=False)

        if self.config.get(DEFAULTSECT, "debug", False):
            keys = request_environ.keys()
            keys.sort()
            for key in keys:
                log.debug('%s: %s', key, repr(request_environ[key]))

        log.info('Starting Captain Hooks.')

        # Fix Github client to use the genvent concurrent HTTP client classes
        Requester.injectConnectionClasses(CachingHTTPConnection, CachingHTTPSConnection)

        self.__flask = Flask(__name__)

        services.get(DatabaseService).boot(self)
        services.get(WebHookEndpoint).boot(self)
        services.get(ApiEndpoint).boot(self)

        return self.__flask

    def run(self):
        debug = self.config.getboolean(DEFAULTSECT, "debug", False)

        run_simple(
            hostname=self.config.get(DEFAULTSECT, "listen_address", "0.0.0.0"),
            port=self.config.getint(DEFAULTSECT, "port", 8888),
            application=self,
            use_reloader=debug,
            use_debugger=debug
        )

    def __call__(self, environ, start_response):
        return self.setup(environ).__call__(environ, start_response)


application = ToolsHooksApp()

if __name__ == '__main__':
    application.run()
