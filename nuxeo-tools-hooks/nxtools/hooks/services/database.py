from mongoengine.connection import connect
from nxtools import ServiceContainer, services
from nxtools.hooks.services import BootableService
from nxtools.hooks.services.config import Config


@ServiceContainer.service
class DatabaseService(BootableService):

    def __init__(self):
        self._config = services.get(Config)

    def boot(self, app):
        """ :type app: nxtools.hooks.app.ToolsHooksApp """
        self.connect()

    @property
    def config_section(self):
        return type(self).__name__

    def connect(self):
        connection_url = self._config.get(self.config_section, "connection_url")
        connect(host=connection_url)
