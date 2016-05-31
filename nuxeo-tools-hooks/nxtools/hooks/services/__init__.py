from abc import ABCMeta
from nxtools import services
from nxtools.hooks.services.config import Config


class AbstractService(object):
    __metaclass__ = ABCMeta

    def config(self, key, default=None):
        return services.get(Config).get(Config.get_section(self), key, default)
