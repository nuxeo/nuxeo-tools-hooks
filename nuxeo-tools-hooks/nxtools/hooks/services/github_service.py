"""
(C) Copyright 2016 Nuxeo SA (http://nuxeo.com/) and contributors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
you may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Contributors:
    Pierre-Gildas MILLON <pgmillon@nuxeo.com>
"""

from httplib import HTTPException
from operator import itemgetter

import logging
import gevent
import re

from github.GithubException import UnknownObjectException, GithubException
from github.MainClass import Github
from github.Organization import Organization
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

    def check_oauth_token(self, token):
        github = Github(token)
        try:
            github.get_user().id
        except GithubException, e:
            log.warn('Could not check oauth token "%s": %s', token, e)
            return False

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

    def create_pullrequest(self, organization, repository, pull_request):

        stored_pr = StoredPullRequest.objects(
            organization=organization.login,
            repository=repository.name,
            pull_number=pull_request.number
        ).first()

        if stored_pr is None:
            stored_pr = StoredPullRequest(
                organization=organization.login,
                repository=repository.name,
                pull_number=pull_request.number,
            )

        stored_pr.branch = pull_request.head.ref
        stored_pr.head_commit = pull_request.head.sha
        stored_pr.created_at = pull_request.created_at
        stored_pr.save()
        log.info('Pull request %s/%s/pull/%d saved', organization.login, repository.name, pull_request.number)

    def get_pullrequest(self, stored_pullrequest):
        github = services.get(GithubService)  # type: GithubService
        jira = services.get(JiraService)  # type: JiraService

        try:
            organization = github.get_organization(stored_pullrequest.organization)
            repository = organization.get_repo(stored_pullrequest.repository)
            pullrequest = repository.get_pull(stored_pullrequest.pull_number)
            head_commit = repository.get_commit(pullrequest.head.sha)
            jira_key = jira.get_issue_id_from_branch(stored_pullrequest.branch)
            jira_issue = jira.get_issue(jira_key)

            return {
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
                'review_status': ([{
                                      'state': status.state,
                                      'description': status.description,
                                      'target': status.target_url,
                                      'context': status.context
                                  } for status in head_commit.get_statuses()
                                  if status.context.startswith("code-review/")] or [None])[0],
                'repository': repository.name,
                'state': pullrequest.state,
                'title': pullrequest.title,
                'updated_at': pullrequest.updated_at.isoformat() if pullrequest.updated_at else None,
                'url': pullrequest.url,
                'user': pullrequest.user.login
            }
        except (JIRAError, GithubException, HTTPException), e:
            log.warn('list_pull_requests: Failed to fetch data of %s/%s/pull/%s: %s',
                     stored_pullrequest.organization, stored_pullrequest.repository, stored_pullrequest.pull_number, e)
            return None

    def list_pull_requests(self):
        pullrequests = []

        def append(stored_pr):
            api_pullrequest = self.get_pullrequest(stored_pr)
            if api_pullrequest is not None:
                pullrequests.append(api_pullrequest)

        try:
            gevent.joinall([gevent.spawn(append, stored_pr) for stored_pr in
                            StoredPullRequest.objects()])
        except OperationError, e:
            log.warn('list_pull_requests: Failed to fetch data from database: %s', e)
            raise Exception(e)

        return sorted(pullrequests, key=itemgetter('created_at'))

    def sync_repository_pullrequests(self, repository):
        organization_name = repository.organization.login
        repository_name = repository.name

        log.info('Syncing pull requests of %s/%s', organization_name, repository_name)
        try:
            opened_pulls = repository.get_pulls()
            pulls_count = 0

            # Fix no count available on pulls list
            for _ in opened_pulls:
                pulls_count += 1

            if pulls_count > 0:
                log.info('Updating %s/%s pull requests: %s',
                         organization_name, repository_name, ", ".join([str(pull.number) for pull in opened_pulls]))

                gevent.joinall([gevent.spawn(
                    lambda pr: self.create_pullrequest(repository.organization, repository, pr), pullrequest)
                                for pullrequest in opened_pulls])

                uncertain_pulls = StoredPullRequest.objects(
                    organization=organization_name,
                    repository=repository_name,
                    pull_number__nin=[pull.number for pull in opened_pulls])

                if uncertain_pulls:
                    log.info('No intel fetched for %s/%s pull requests: %s',
                             organization_name, repository_name, ", ".join([str(pull.pull_number) for pull in uncertain_pulls]))

                    for stored_pull in uncertain_pulls:
                        log.info('Checking status of %s/%s/pull/%d',
                                 organization_name, repository_name, stored_pull.pull_number)

                        original_pull = repository.get_pull(stored_pull.pull_number)
                        if "closed" == original_pull.state:
                            log.info('%s/%s/pull/%d is closed, removing it',
                                     organization_name, repository_name, stored_pull.pull_number)
                            stored_pull.delete()

        except (HTTPException, GithubException, OperationError), e:
            log.warn('sync_pull_requests: Failed to fetch pull requests of repository %s/%s: %s',
                     organization_name, repository_name, e)

    def sync_pull_requests(self):
        for organization_name in re.sub(r"\s+", "", self.config('sync_pullrequests_organizations', ''),
                                        flags=re.UNICODE).split(','):
            try:
                organization = self.get_organization(organization_name)  # type: Organization

                gevent.joinall([gevent.spawn(
                    lambda repo: self.sync_repository_pullrequests(repo), repository)
                                for repository in organization.get_repos()])

            except (HTTPException, GithubException, NoSuchOrganizationException), e:
                log.warn('sync_pull_requests: Failed to fetch repositories of %s: %s', organization_name, e)

    def setup_webhooks(self, organization_name, repository_name, hooks_config):
        try:
            organization = self.get_organization(organization_name)  # type: Organization
            repository = organization.get_repo(repository_name)  # type: Repository
            hooks = repository.get_hooks()

            if 'absent' in hooks_config:
                for hook in list(hooks):
                    if hook.name in hooks_config['absent'] or hook.url in [h['url'] for h in hooks_config['absent']
                                                                           if type(h) is dict and 'url' in h]:
                        hook.delete()
                        hooks.remove(hook)
            if 'present' in hooks_config:
                for hook in hooks:
                    [hook.edit(h['name'], h['config'], h['events'], active=h['active'])
                     for h in hooks_config['present'] if h['name'] == hook.name]
                [repository.create_hook(h['name'], h['config'], h['events'], h['active'])
                 for h in hooks_config['present'] if h['name'] not in [hook.name for hook in hooks]]

        except (HTTPException, GithubException, NoSuchOrganizationException), e:
            log.warn('setup_webhooks: Failed setup webhooks of %s/%s: %s', organization_name, repository_name, e)
            raise Exception(e)
