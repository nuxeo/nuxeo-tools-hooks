#!/usr/bin/env python

import logging
import os

from flask.app import Flask
from nxtools import services
from nxtools.hooks import DEFAULTSECT
from nxtools.hooks.endpoints.api import ApiEndpoint
from nxtools.hooks.endpoints.webhook import WebHookEndpoint
from nxtools.hooks.services.config import Config
from nxtools.hooks.services.database import DatabaseService


class ToolsHooksApp(object):

    def __init__(self):
        self.__flask = None

        config_file = os.getenv(Config.ENV_PREFIX + "CONF", os.getcwd() + "/conf/nuxeo-tools-hooks.ini")
        services.add(Config(config_file))

    @property
    def config(self):
        return services.get(Config)

    @property
    def flask(self):
        """ :rtype: flask.app.Flask"""
        return self.__flask

    def setup(self):
        log_file = self.config.get(DEFAULTSECT, "log_file")
        if log_file and not os.path.exists(os.path.dirname(log_file)):
            os.makedirs(os.path.dirname(log_file))

        logging.basicConfig(
            filename=log_file,
            level=logging._levelNames[self.config.get(DEFAULTSECT, "log_level", "INFO").upper()])

        self.__flask = Flask(__name__)

        services.get(DatabaseService).boot(self)
        services.get(WebHookEndpoint).boot(self)
        services.get(ApiEndpoint).boot(self)

        return self.__flask

    def run(self):
        app = self.setup()

        app.run(
            host=self.config.get(DEFAULTSECT, "listen_address", "0.0.0.0"),
            port=self.config.getint(DEFAULTSECT, "port", 8888),
            debug=self.config.getboolean(DEFAULTSECT, "debug", False))

    def __call__(self, environ, start_response):
        return self.setup().__call__(environ, start_response)

application = ToolsHooksApp()

if __name__ == '__main__':
    application.run()
