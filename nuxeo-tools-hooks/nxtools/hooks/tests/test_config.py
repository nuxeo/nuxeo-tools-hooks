import os

from nxtools import services
from nxtools.hooks import DEFAULTSECT
from nxtools.hooks.services.config import Config
from nxtools.hooks.tests import HooksTestCase


class ConfigTest(HooksTestCase):

    CONFIG_KEY = 'overloaded'
    INTEGER_KEY = 'integer_key'
    BOOLEAN_KEY = 'boolean_key'

    CONFIG_VALUE = 'Config'
    ENV_VALUE = 'Environment'
    REQUEST_VALUE = 'Request'

    CUSTOM_SERVICE = 'CustomService'

    def test_config(self):
        config = services.get(Config)

        self.assertEqual(1, len(config.items(DEFAULTSECT)))
        self.assertEqual(3, len(config.items(ConfigTest.CUSTOM_SERVICE)))

        self.assertEqual(42, config.getint(ConfigTest.CUSTOM_SERVICE, ConfigTest.INTEGER_KEY, 666))
        self.assertEqual(True, config.getboolean(ConfigTest.CUSTOM_SERVICE, ConfigTest.BOOLEAN_KEY, False))

    def test_config_overload(self):
        config = services.get(Config)  # type: Config
        self.assertEqual(ConfigTest.CONFIG_VALUE, config.get(DEFAULTSECT, ConfigTest.CONFIG_KEY))

        os.environ[Config.ENV_PREFIX + ConfigTest.CONFIG_KEY.upper()] = ConfigTest.ENV_VALUE
        self.assertEqual(ConfigTest.ENV_VALUE, config.get(DEFAULTSECT, ConfigTest.CONFIG_KEY))

        config.set_request_environ({
            Config.ENV_PREFIX + ConfigTest.CONFIG_KEY.upper(): ConfigTest.REQUEST_VALUE
        })
        self.assertEqual(ConfigTest.REQUEST_VALUE, config.get(DEFAULTSECT, ConfigTest.CONFIG_KEY))
