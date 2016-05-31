import re

from jira.client import JIRA
from nxtools import ServiceContainer
from nxtools.hooks.services import AbstractService


@ServiceContainer.service
class JiraService(AbstractService):

    def __init__(self):
        if "basic" == self.config("auth_type"):
            self.__jira_client = JIRA(self.config("url"),
                                      basic_auth=(self.config("basic_username"), self.config("basic_password")))

    def get_issue(self, id):
        """
        :rtype: jira.resources.Issue
        """
        return self.__jira_client.issue(id)

    def get_issue_id_from_branch(self, branch_name):
        matches = re.compile("[a-z]+-([A-Z]+-[0-9]+)-.*").match(branch_name)
        if matches:
            return matches.group(1)
        return None
