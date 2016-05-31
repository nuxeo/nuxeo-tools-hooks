from ConfigParser import SafeConfigParser

from types import ClassType

import os


class Config(object):

    ENV_PREFIX = "NXTOOLS_HOOKS_"

    @staticmethod
    def get_section(service):
        if isinstance(service, type) or isinstance(service, ClassType):
            return service.__name__
        else:
            return type(service).__name__

    def __init__(self, config_file):
        self._config = SafeConfigParser()
        self._config.read(config_file)

    def get_env_key_name(self, key, section=None):
        key = key.upper()
        if section and section != "general":
            key = section.replace("Service", "_").upper() + key
        return Config.ENV_PREFIX + key

    def get(self, section, key, default=None):
        config_value = default
        if self._config.has_option(section, key):
            config_value = self._config.get(section, key)
        return os.getenv(self.get_env_key_name(key, section), config_value)

    def items(self, section, defaults=None):
        items = defaults or {}
        if self._config.has_section(section):
            items.update({k: v for k, v in self._config.items(section)})
        items.update({k: os.getenv(self.get_env_key_name(k, section), v) for k, v in items.iteritems()})
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
