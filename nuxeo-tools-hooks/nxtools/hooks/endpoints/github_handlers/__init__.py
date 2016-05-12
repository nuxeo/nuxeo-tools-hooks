from abc import ABCMeta, abstractmethod


class AbstractGithubHandler(object):
    __metaclass__ = ABCMeta

    def __init__(self, hook):
        self.__hook = hook
        self.__config_section = type(self).__name__

    @abstractmethod
    def handle(self, payload_body):
        pass

    @property
    def hook(self):
        """
        :rtype: nxtools.hooks.endpoints.github_hook.GithubHookEndpoint
        """
        return self.__hook

    @property
    def config_section(self):
        return self.__config_section

    def get_config(self, key, default=None):
        return self.hook.config.get(self.config_section, key, default)
