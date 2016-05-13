from abc import ABCMeta, abstractmethod

from flask.blueprints import Blueprint
from flask.globals import request
from nxtools import services
from nxtools.hooks.services.config import Config


class AbstractWebHook(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def can_handle(self, headers, body):
        pass


class NoSuchHookException(Exception):
    pass


class WebHookEndpoint(object):

    __blueprint = Blueprint('webhook', __name__)

    def __init__(self):
        self.__handlers = []

    @staticmethod
    def blueprint():
        return WebHookEndpoint.__blueprint

    @property
    def config(self):
        return services.get(Config)

    @property
    def config_section(self):
        return type(self).__name__

    @property
    def handlers(self):
        return self.__handlers

    def add_handler(self, handler):
        self.__handlers.append(handler)

    @staticmethod
    @__blueprint.route('/')
    def route():
        self = services.get(WebHookEndpoint)

        for handler in self.handlers:
            if handler.can_handle(request.headers, request.data):
                return handler.handle(request.headers, request.data)

        raise NoSuchHookException()

        # return self.config.get(self.config_section, "key", "Hello World")

