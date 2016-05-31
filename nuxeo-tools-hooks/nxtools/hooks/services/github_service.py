from github.GithubException import UnknownObjectException
from github.MainClass import Github
from nxtools import ServiceContainer, services
from nxtools.hooks.entities.github_entities import OrganizationWrapper
from nxtools.hooks.services import AbstractService
from nxtools.hooks.services.config import Config


class NoSuchOrganizationException(Exception):
    def __init__(self, organization):
        super(NoSuchOrganizationException, self).__init__("Unknown organization '%s'" % organization)


@ServiceContainer.service
class GithubService(AbstractService):

    CONFIG_OAUTH_PREFIX = "oauth_token_"

    def __init__(self):
        self.__organizations = {}

    def get_organization(self, name):
        """
        :rtype: nxtools.hooks.entities.github_entities.OrganizationWrapper
        """

        github = Github(self.config(GithubService.CONFIG_OAUTH_PREFIX + name))

        if name not in self.__organizations:
            try:
                self.__organizations[name] = OrganizationWrapper(github.get_organization(name))
            except UnknownObjectException:
                raise NoSuchOrganizationException(name)
        return self.__organizations[name]

