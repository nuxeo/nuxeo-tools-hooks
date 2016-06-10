import logging

from mongoengine.connection import connect
from nxtools import ServiceContainer, services
from nxtools.hooks.services import BootableService
from nxtools.hooks.services.config import Config

log = logging.getLogger(__name__)


@ServiceContainer.service
class DatabaseService(BootableService):

    def __init__(self):
        self._config = services.get(Config)

    @property
    def db_url(self):
        return self._config.get(self.config_section, "connection_url")

    def boot(self, app):
        """ :type app: nxtools.hooks.app.ToolsHooksApp """

        log.info(' * Connecting to database backend: ' + self.db_url)

        self.connect()

    @property
    def config_section(self):
        return type(self).__name__

    def connect(self):
        connection_url = self.db_url
        connect(host=connection_url)
