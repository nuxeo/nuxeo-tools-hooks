from ConfigParser import SafeConfigParser

import os


class Config(object):

    ENV_PREFIX = "NXTOOLS_HOOKS_"

    def __init__(self, config_file):
        self._config = SafeConfigParser()
        self._config.read(config_file)

    def get(self, section, key, default=None):
        config_value = default
        if self._config.has_option(section, key):
            config_value = self._config.get(section, key)
        return os.getenv(Config.ENV_PREFIX + key.upper(), config_value)

    def items(self, section, defaults=None):
        items = defaults or {}
        if self._config.has_section(section):
            items.update({k: v for k, v in self._config.items(section)})
        items.update({k: os.getenv(Config.ENV_PREFIX + k.upper(), v) for k, v in items.iteritems()})
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
