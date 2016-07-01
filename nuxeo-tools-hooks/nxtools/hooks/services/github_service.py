from httplib import HTTPException

import logging

import re

from github.GithubException import UnknownObjectException, GithubException
from github.MainClass import Github
from github.Organization import Organization
from github.PullRequest import PullRequest
from github.Repository import Repository
from jira.exceptions import JIRAError
from mongoengine.errors import OperationError
from nxtools import ServiceContainer, services
from nxtools.hooks.entities.db_entities import StoredPullRequest
from nxtools.hooks.entities.github_entities import OrganizationWrapper
from nxtools.hooks.services import AbstractService
from nxtools.hooks.services.jira_service import JiraService

log = logging.getLogger(__name__)


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

    def list_pull_requests(self):
        github = services.get(GithubService)  # type: GithubService
        jira = services.get(JiraService)  # type: JiraService
        pullrequests = []

        try:
            for stored_pr in StoredPullRequest.objects():
                try:
                    organization = github.get_organization(stored_pr.organization)
                    repository = organization.get_repo(stored_pr.repository)
                    pullrequest = repository.get_pull(stored_pr.pull_number)
                    head_commit = repository.get_commit(pullrequest.head.sha)
                    jira_key = jira.get_issue_id_from_branch(stored_pr.branch)
                    jira_issue = jira.get_issue(jira_key)
                    pullrequests.append({
                        'additions': pullrequest.additions,
                        'assignee': pullrequest.assignee.login if pullrequest.assignee else None,
                        'base': pullrequest.base.ref,
                        'body': pullrequest.body,
                        'changed_files': pullrequest.changed_files,
                        'closed_at': pullrequest.closed_at.isoformat() if pullrequest.closed_at else None,
                        'comments': pullrequest.comments,
                        'comments_url': pullrequest.comments_url,
                        'commits': pullrequest.commits,
                        'commits_url': pullrequest.commits_url,
                        'created_at': pullrequest.created_at.isoformat(),
                        'deletions': pullrequest.deletions,
                        'diff_url': pullrequest.diff_url,
                        'head': pullrequest.head.ref,
                        'html_url': pullrequest.html_url,
                        'id': pullrequest.id,
                        'issue_url': pullrequest.issue_url,
                        'jira_key': jira_key,
                        'jira_summary': jira_issue.fields.summary,
                        'merge_commit_sha': pullrequest.merge_commit_sha,
                        'mergeable': pullrequest.mergeable,
                        'mergeable_state': pullrequest.mergeable_state,
                        'merged': pullrequest.merged,
                        'merged_at': pullrequest.merged_at.isoformat() if pullrequest.merged_at else None,
                        'merged_by': pullrequest.merged_by.login if pullrequest.merged_by else None,
                        'milestone': pullrequest.milestone.id if pullrequest.milestone else None,
                        'number': pullrequest.number,
                        'organization': organization.login,
                        'other_statuses': [{
                           'state': status.state,
                           'description': status.description,
                           'target': status.target_url,
                           'context': status.context
                                           } for status in head_commit.get_statuses()
                                           if not status.context.startswith("code-review/")],
                        'patch_url': pullrequest.patch_url,
                        'review_comment_url': pullrequest.review_comment_url,
                        'review_comments': pullrequest.review_comments,
                        'review_status': [{
                            'state': status.state,
                            'description': status.description,
                            'target': status.target_url,
                            'context': status.context
                                          } for status in head_commit.get_statuses()
                                          if status.context.startswith("code-review/")][0],
                        'repository': repository.name,
                        'state': pullrequest.state,
                        'title': pullrequest.title,
                        'updated_at': pullrequest.updated_at.isoformat() if pullrequest.updated_at else None,
                        'url': pullrequest.url,
                        'user': pullrequest.user.login
                    })
                except (JIRAError, GithubException, HTTPException), e:
                    log.warn('list_pull_requests: Failed to fetch data of %s/%s/pull/%s: %s',
                             stored_pr.organization, stored_pr.repository, stored_pr.pull_number, e)
        except OperationError, e:
            log.warn('list_pull_requests: Failed to fetch data from database: %s', e)
            raise Exception(e)

        return pullrequests

    def sync_pull_requests(self):

        for organization_name in re.sub(r"\s+", "", self.config('sync_pullrequests_organizations', ''),
                                        flags=re.UNICODE).split(','):
            try:
                organization = self.get_organization(organization_name)  # type: Organization
                for repository in organization.get_repos():  # type: Repository
                    try:
                        log.info('Syncing pull requests of %s/%s', organization_name, repository.name)
                        for pull_request in repository.get_pulls():  # type: PullRequest
                            stored_pr = StoredPullRequest(
                                branch=pull_request.head.ref,
                                organization=organization.login,
                                repository=repository.name,
                                head_commit=pull_request.head.sha,
                                pull_number=pull_request.number
                            )

                            stored_pr.save()

                    except (HTTPException, GithubException, OperationError), e:
                        log.warn('sync_pull_requests: Failed to fetch pull requests of repository %s/%s: %s',
                                 organization_name, repository.name, e)

            except (HTTPException, GithubException, NoSuchOrganizationException), e:
                log.warn('sync_pull_requests: Failed to fetch repositories of %s: %s', organization_name, e)
