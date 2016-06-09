import pkgutil
import sys
import types

from abc import ABCMeta, abstractmethod
from flask.blueprints import Blueprint
from flask.globals import request
from nxtools import services, ServiceContainer
from nxtools.hooks.endpoints import AbstractEndpoint
from nxtools.hooks.endpoints.webhook.github_handlers import AbstractGithubHandler
from nxtools.hooks.services import BootableService


class AbstractWebHook(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def can_handle(self, headers, body):
        pass


class NoSuchHookException(Exception):
    pass


@ServiceContainer.service
class WebHookEndpoint(AbstractEndpoint, BootableService):

    __blueprint = Blueprint('webhook', __name__)

    def boot(self, app):
        """ :type app: nxtools.hooks.app.ToolsHooksApp """
        app.flask.register_blueprint(WebHookEndpoint.blueprint(), url_prefix="/hook")

    @staticmethod
    def blueprint():
        return WebHookEndpoint.__blueprint

    @staticmethod
    @__blueprint.route('/', methods=['POST'])
    def route():
        return services.get(WebHookEndpoint).do_route()

    def __init__(self):
        super(WebHookEndpoint, self).__init__()

        loaded = [key for key, value in sys.modules.items()
                  if key.startswith(__name__) and isinstance(value, types.ModuleType)]

        for loader, module_name, is_pkg in pkgutil.iter_modules(__path__, __name__ + "."):
            if module_name.endswith("_hook") and module_name not in loaded:
                loader.find_module(module_name).load_module(module_name)

    def do_route(self):
        for handler in [handler for handler in self.hooks
                        if handler.can_handle(request.headers, request.data)]:
            return handler.handle(request.headers, request.data)

        raise NoSuchHookException()

    @property
    def hooks(self):
        return [handler for t, n, handler in services.list(AbstractWebHook)]
