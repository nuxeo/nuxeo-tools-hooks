from nxtools import services
from nxtools.hooks.services.config import Config


class AbstractEndpoint(object):

    @property
    def config(self):
        return services.get(Config)

    @property
    def config_section(self):
        return type(self).__name__
