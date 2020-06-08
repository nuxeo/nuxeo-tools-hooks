"""
(C) Copyright 2016-2020 Nuxeo SA (http://nuxeo.com/) and contributors.

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
    Anahide Tchertchian <at@nuxeo.com>
"""

from ConfigParser import SafeConfigParser

import logging

from nxtools import ServiceContainer
from nxtools.hooks import DEFAULTSECT
from types import ClassType

import os
import re

log = logging.getLogger(__name__)


@ServiceContainer.service
class Config(object):

    ENV_PREFIX = "NXTOOLS_HOOKS_"
    CONFIG_FILE_KEY = 'CONF'

    @staticmethod
    def get_section(service):
        if isinstance(service, type) or isinstance(service, ClassType):
            return service.__name__
        else:
            return type(service).__name__

    @staticmethod
    def get_env_key_name(key, section=None):
        key = key.upper()
        if section and section != "general":
            key = section.replace("Service", "").upper() + "_" + key
        return Config.ENV_PREFIX + key

    def __init__(self):
        self._config = None
        self.request_env = {}

        self.reload()

    def reload(self):
        self._config = SafeConfigParser()

        config_file = self.get(DEFAULTSECT, Config.CONFIG_FILE_KEY, os.getcwd() + '/conf/nuxeo-tools-hooks.ini')
        log.info('Loading config file: %s', config_file)

        self._config.read(config_file)

    def set_request_environ(self, environ):
        self.request_env = environ
        self.reload()

    def get(self, section, key, default=None):
        config_value = default
        env_key = Config.get_env_key_name(key, section)

        if self._config.has_option(section, key):
            config_value = self._config.get(section, key)

        value = self.request_env.get(env_key, os.getenv(env_key, config_value))

        log.debug('Get [%s] %s, default=%s, env_key=%s, request_value=%s, os_value=%s, config_value=%s, value=%s',
                  section, key, default, env_key, self.request_env.get(env_key), os.getenv(env_key), config_value, value)

        return value

    def items(self, section, defaults=None):
        items = defaults or {}
        if self._config.has_section(section):
            items.update({k: v for k, v in self._config.items(section)})
        items.update({k: os.getenv(Config.get_env_key_name(k, section), v) for k, v in items.iteritems()})
        return items

    # From ConfigParser.py

    _boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    def getint(self, section, key, default=None):
        return int(self.get(section, key, default))

    def getboolean(self, section, key, default=None):
        config_value = default
        if self._config.has_option(section, key):
            config_value = self._config.get(section, key)
        config_value = os.getenv(Config.ENV_PREFIX + key.upper(), config_value)

        if isinstance(config_value, bool):
            return config_value

        if config_value.lower() not in self._boolean_states:
            raise ValueError('Not a boolean: %s' % config_value)
        return self._boolean_states[config_value.lower()]

    def getlist(self, section, key, default=None):
        config = self.get(section, key, default)
        if config:
            config = config.replace('\n', ',')
            config = re.sub(r"\s+", "", config, flags=re.UNICODE).split(",")
            config = filter(None, config)
            config = filter(lambda x: not x.startswith('#'), config)
        return config
