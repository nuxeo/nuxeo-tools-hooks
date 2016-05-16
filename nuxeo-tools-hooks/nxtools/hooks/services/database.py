from mongoengine.connection import connect
from nxtools import ServiceContainer, services
from nxtools.hooks.services.config import Config


@ServiceContainer.service
class DatabaseService(object):

    def __init__(self):
        self._config = services.get(Config)

    @property
    def config_section(self):
        return type(self).__name__

    def connect(self):
        connection_url = self._config.get(self.config_section, "connection_url")
        connect(host=connection_url)
