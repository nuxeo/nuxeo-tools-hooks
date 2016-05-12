#!/usr/bin/env python

import logging

import os

from flask.app import Flask
from nxtools.hooks import DEFAULTSECT
from nxtools.hooks.services.config import Config

config_file = os.getenv(Config.ENV_PREFIX + "CONF", os.getcwd() + "/conf/nuxeo-tools-hooks.ini")
config = Config(config_file)

log_file = config.get(DEFAULTSECT, "log_file")
if not os.path.exists(os.path.dirname(log_file)):
    os.makedirs(os.path.dirname(log_file))

logging.basicConfig(
    filename=log_file,
    level=logging._levelNames[config.get(DEFAULTSECT, "log_level", "INFO").upper()])


app = Flask(__name__)

if __name__ == '__main__':
    app.run(
        host=config.get(DEFAULTSECT, "listen_address", "0.0.0.0"),
        port=config.getint(DEFAULTSECT, "port", 8888),
        debug=config.getboolean(DEFAULTSECT, "debug", False))
