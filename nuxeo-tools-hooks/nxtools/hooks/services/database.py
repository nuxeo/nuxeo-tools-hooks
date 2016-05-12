from mongoengine.connection import connect


class DatabaseService(object):

    def __init__(self, config):
        """
        :type config : nxtools.hooks.services.config.Config
        """
        self._config = config

    @property
    def config_section(self):
        return type(self).__name__

    def connect(self):
        connection_url = self._config.get(self.config_section, "connection_url")
        connect(host=connection_url)
