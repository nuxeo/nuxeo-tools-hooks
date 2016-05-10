# coding=UTF-8

import json

from abc import ABCMeta, abstractmethod
from github.MainClass import Github
from github.GithubException import UnknownObjectException
from nxtools.hooks.entities.github_entities import OrganizationWrapper


class UnknownEventException(Exception):
    def __init__(self, event):
        super(UnknownEventException, self).__init__("Unknown event '%s'" % event)


class InvalidPayloadException(Exception):
    def __init__(self, previous):
        self.previous = previous

        super(InvalidPayloadException, self).__init__()


class NoSuchOrganizationException(Exception):
    def __init__(self, organization):
        super(NoSuchOrganizationException, self).__init__("Unknown organization '%s'" % organization)


class AbstractGithubHandler(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def handle(self, payload_body):
        pass

    @property
    def hook(self):
        """
        :rtype: nxtools.hooks.webhook.github_hook.GithubHook
        """
        return self._hook

    def __init__(self, hook):
        object.__init__(self)
        self._hook = hook


class GithubHook(object):

    eventSource = "Github"
    payloadHeader = "X-GitHub-Event"
    github_events = {}

    _handlers = {}
    """:type : dict[str, list[AbstractGithubHandler]]"""

    def __init__(self):

        self._organizations = {}

        # TODO: https://github.com/organizations/nuxeo-sandbox/settings/applications
        self.github = Github("")

    @staticmethod
    def add_handler(event, handler):
        """
        @type event : str
        @type handler : nxtools.hooks.webhook.github_hook.AbstractGithubHandler
        """
        if event not in GithubHook._handlers:
            GithubHook._handlers[event] = [handler]
        else:
            GithubHook._handlers[event].append(handler)

    @staticmethod
    def get_handlers(event):
        """
        :rtype: list[nxtools.hooks.webhook.github_hook.AbstractGithubHandler]
        @type event : str
        """
        return GithubHook._handlers[event] if event in GithubHook._handlers else []

    def get_organization(self, name):
        """
        :rtype: nxtools.hooks.entities.github_entities.OrganizationWrapper
        """
        if name not in self._organizations:
            try:
                self._organizations[name] = OrganizationWrapper(self.github.get_organization(name))
            except UnknownObjectException:
                raise NoSuchOrganizationException(name)
        return self._organizations[name]

    def handle(self, headers, body):
        """
        @type headers : dict[str, str]
        @type body : str
        """

        if GithubHook.payloadHeader in headers:
            payload_event = headers[GithubHook.payloadHeader]
            handlers = GithubHook.get_handlers(payload_event)

            if handlers:
                json_body = json.loads(body)

                for handler in handlers:
                    handler.handle(json_body)
            else:
                raise UnknownEventException(payload_event)
