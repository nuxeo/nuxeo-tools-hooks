from ConfigParser import SafeConfigParser

import os


class Config(object):

    def __init__(self, config_file):
        self._config = SafeConfigParser()
        self._config.read(config_file)

    def get(self, section, key, default=None, env_key=None):
        config_value = default
        if self._config.has_option(section, key):
            config_value = self._config.get(section, key)
        return os.getenv(env_key, config_value)
