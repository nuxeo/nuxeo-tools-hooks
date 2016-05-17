from abc import ABCMeta, abstractmethod

from flask.blueprints import Blueprint
from flask.globals import request
from nxtools import services, ServiceContainer
from nxtools.hooks.endpoints import AbstractEndpoint
from nxtools.hooks.services.config import Config


class AbstractWebHook(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def can_handle(self, headers, body):
        pass


class NoSuchHookException(Exception):
    pass


@ServiceContainer.service
class WebHookEndpoint(AbstractEndpoint):

    __blueprint = Blueprint('webhook', __name__)

    @staticmethod
    def blueprint():
        return WebHookEndpoint.__blueprint

    @property
    def config(self):
        return services.get(Config)

    @property
    def config_section(self):
        return type(self).__name__

    @staticmethod
    def get_hooks():
        return [handler for t, n, handler in services.list(AbstractWebHook)]

    @staticmethod
    @__blueprint.route('/', methods=['POST'])
    def route():
        for handler in [handler for handler in WebHookEndpoint.get_hooks()
                        if handler.can_handle(request.headers, request.data)]:
            return handler.handle(request.headers, request.data)

        raise NoSuchHookException()
