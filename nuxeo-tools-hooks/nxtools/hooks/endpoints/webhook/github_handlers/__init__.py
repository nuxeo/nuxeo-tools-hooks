from abc import ABCMeta, abstractmethod
from nxtools import services
from nxtools.hooks.services.config import Config


class AbstractGithubHandler(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.__config_section = type(self).__name__

    @abstractmethod
    def handle(self, payload_body):
        pass

    @abstractmethod
    def can_handle(self, payload_event):
        pass

    @property
    def config_section(self):
        return self.__config_section

    def get_config(self, key, default=None):
        return services.get(Config).get(self.config_section, key, default)
