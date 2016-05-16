from abc import ABCMeta, abstractmethod
from nxtools import services
from nxtools.hooks.endpoints.webhook.github_hook import GithubHook


class AbstractGithubHandler(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.__config_section = type(self).__name__

    @abstractmethod
    def handle(self, payload_body):
        pass

    @property
    def hook(self):
        """
        :rtype: nxtools.hooks.endpoints.github_hook.GithubHookEndpoint
        """
        return services.get(GithubHook)

    @property
    def config_section(self):
        return self.__config_section

    def get_config(self, key, default=None):
        return self.hook.config.get(self.config_section, key, default)
