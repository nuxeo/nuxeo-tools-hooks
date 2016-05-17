# coding=UTF-8

import json
from io import StringIO

from github.MainClass import Github
from github.GithubException import UnknownObjectException
from nxtools import services, ServiceContainer
from nxtools.hooks.endpoints.webhook import AbstractWebHook
from nxtools.hooks.endpoints.webhook.github_handlers import AbstractGithubHandler
from nxtools.hooks.entities.github_entities import OrganizationWrapper
from nxtools.hooks.services.config import Config


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


@ServiceContainer.service
class GithubHook(AbstractWebHook):

    eventSource = "Github"
    payloadHeader = "X-GitHub-Event"
    github_events = {}

    """:type : dict[str, list[AbstractGithubHandler]]"""

    def __init__(self):
        self._organizations = {}

        # TODO: https://github.com/organizations/nuxeo-sandbox/settings/applications
        self.github = Github("")

    def can_handle(self, headers, body):
        return GithubHook.payloadHeader in headers

    @property
    def config(self):
        """
        :rtype: nxtools.hooks.services.config.Config
        """
        return services.get(Config)

    @property
    def handlers(self):
        return [handler for t, n, handler in services.list(AbstractGithubHandler)]

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
            handlers = [handler for handler in self.handlers if handler.can_handle(payload_event)]

            if handlers:
                json_body = json.loads(body)
                response = StringIO()
                status = 200

                for handler in handlers:
                    s, r = handler.handle(json_body)
                    response.writelines(unicode(r))
                    status = max(status, s)

                return response.getvalue(), status
            else:
                raise UnknownEventException(payload_event)
