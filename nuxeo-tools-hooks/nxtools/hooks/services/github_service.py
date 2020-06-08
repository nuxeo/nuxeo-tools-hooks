"""
(C) Copyright 2016-2019 Nuxeo SA (http://nuxeo.com/) and contributors.

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
    jcarsique
"""

from httplib import HTTPException
from operator import itemgetter

import gevent
import json
import logging
import re
import operator
import socket

from github.GithubException import UnknownObjectException, GithubException
from github.Commit import Commit
from github.File import File
from github.Hook import Hook
from github.IssueComment import IssueComment
from github.MainClass import Github
from github.Organization import Organization
from github.Repository import Repository
from jira.exceptions import JIRAError
from lxml.html import html5parser, XHTML_NAMESPACE
from lxml.etree import LxmlError
from mongoengine.errors import OperationError
from nxtools import ServiceContainer, services
from nxtools.hooks.entities.db_entities import StoredPullRequest
from nxtools.hooks.entities.exceptions import SlackException
from nxtools.hooks.entities.github_entities import OrganizationWrapper, RepositoryWrapper, PullRequest
from nxtools.hooks.services import AbstractService
from nxtools.hooks.services.jira_service import JiraService
from slackclient import SlackClient

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

    def get_user(self, login):
        try:
            return Github().get_user(login)
        except Exception, e:
            log.warn('Could not fetch user %s', login)
            raise e

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
        stored_pr.save()

        self.update_pullrequest_with_jira(stored_pr)

        return stored_pr

    def update_pullrequest_with_jira(self, stored_pullrequest):
        jira = services.get(JiraService)  # type: JiraService

        if not stored_pullrequest.jira_key:
            jira_key = stored_pullrequest.jira_key = jira.get_issue_id_from_branch(stored_pullrequest.branch)
            if jira_key is not None:
                jira_issue = jira.get_issue(jira_key, 'summary')
                stored_pullrequest.jira_summary = jira_issue.fields.summary \
                if jira_issue is not None else None

            stored_pullrequest.save()

    def get_pullrequest(self, stored_pullrequest):
        github = services.get(GithubService)  # type: GithubService

        try:
            organization = github.get_organization(stored_pullrequest.organization)
            repository = organization.get_repo(stored_pullrequest.repository)
            pullrequest = repository.get_pull(stored_pullrequest.pull_number)
            head_commit = repository.get_commit(pullrequest.head.sha)

            self.update_pullrequest_with_jira(stored_pullrequest)

            jira_key = stored_pullrequest.jira_key
            jira_issue = stored_pullrequest.jira_summary

            if not jira_key:
                log.warning('get_pullrequest: Could not parse JIRA key for %s/%s/pull/%d', organization.login,
                         repository.name, pullrequest.number)

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
                'jira_summary': jira_issue,
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
                } for status in head_commit.get_statuses()],
                'patch_url': pullrequest.patch_url,
                'review_comment_url': pullrequest.review_comment_url,
                'review_comments': pullrequest.review_comments,
                'review_status': ([{
                    'state': status.state,
                    'description': status.description,
                    'target': status.target_url,
                    'context': status.context
                } for status in head_commit.get_statuses()] or [None])[0],
                'repository': repository.name,
                'state': pullrequest.state,
                'title': pullrequest.title,
                'updated_at': pullrequest.updated_at.isoformat() if pullrequest.updated_at else None,
                'url': pullrequest.url,
                'user': pullrequest.user.login
            }
        except (JIRAError, GithubException, HTTPException, socket.error), e:
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
            raise e

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
                         organization_name, repository_name,
                         ", ".join([str(pull.pull_number) for pull in uncertain_pulls]))

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
        for organization_name in self.configlist('sync_pullrequests_organizations', []):
            try:
                organization = self.get_organization(organization_name)  # type: Organization
                gevent.joinall([gevent.spawn(
                    lambda repo: self.sync_repository_pullrequests(repo), repository)
                    for repository in organization.get_repos()])
            except (HTTPException, GithubException, NoSuchOrganizationException), e:
                log.warn('sync_pull_requests: Failed to fetch repositories of %s: %s', organization_name, e)

    def json_encode_hook(self, hook):
        return json.dumps({
            'id': hook.id,
            'name': hook.name,
            'config': hook.config,
            'events': hook.events,
            'active': hook.active

        })

    def update_webhook(self, hook, hooks_config):
        for h in hooks_config:
            if 'id' in h and h['id'] == hook.id:
                log.debug('Updating %s: %s => %s', hook.url, self.json_encode_hook(hook), h)
                hook.edit(h['name'], h['config'], h['events'], active=h['active'])
                return h
            if 'config' in h:
                if 'url' in h['config'] and 'url' in hook.config and h['config']['url'] == hook.config['url']:
                    log.debug('Updating %s: %s => %s', hook.url, self.json_encode_hook(hook), h)
                    hook.edit(h['name'], h['config'], hook.events + [e for e in h['events'] if e not in hook.events],
                              active=h['active'])
                    return h
        return None

    def setup_webhooks(self, organization_name, repository_name, hooks_config):
        try:
            organization = self.get_organization(organization_name)  # type: Organization
            repository = organization.get_repo(repository_name)  # type: Repository
            hooks = list(repository.get_hooks())

            if 'absent' in hooks_config:
                for hook in list(hooks):  # type: Hook
                    if hook.name in hooks_config['absent'] \
                            or 'url' in hook.config and hook.config['url'] in [h['url'] for h in hooks_config['absent']
                                                                               if type(h) is dict and 'url' in h]:
                        log.debug('Deleting %s: %s', hook.url, self.json_encode_hook(hook))
                        hook.delete()
                        hooks.remove(hook)
            if 'present' in hooks_config:
                todo_config = hooks_config['present']

                for hook in hooks:
                    updated = self.update_webhook(hook, todo_config)
                    if updated is not None:
                        todo_config.remove(updated)

                for h in todo_config:
                    log.debug('Creating %s', h)
                    repository.create_hook(h['name'], h['config'], h['events'], h['active'])

        except (HTTPException, GithubException, NoSuchOrganizationException), e:
            log.warn('setup_webhooks: Failed setup webhooks of %s/%s: %s', organization_name, repository_name, e)
            raise Exception(e)


@ServiceContainer.service
class GithubReviewService(AbstractService):

    def github_notify(self, pull_request):
        """
        :type pull_request: nxtools.hooks.entities.db_entities.StoredPullRequest
        :rtype: github.IssueComment.IssueComment
        """
        jira = services.get(JiraService)
        keys = jira.get_issue_ids_from_pullrequest(pull_request)

        if keys:
            jira_service = services.get(JiraService)  # type: JiraService
            jira_service.github_notify(keys, pull_request)

        parts = []
        if len(keys) == 1:
            parts.append("View issue in JIRA: %s" % self._get_issue_comment(keys[0], jira))
        elif len(keys) > 1:
            parts.append("View issues in JIRA:")
            for key in keys:
                parts.append("- %s" % self._get_issue_comment(key, jira))
        if parts:
            return pull_request.gh_object.create_issue_comment("\n".join(parts))

    def _get_issue_comment(self, key, jira):
        if self.config('include_jira_summary', False):
            # don't leak any Jira private info on GitHub
            issue = jira.get_issue_anonymous(key, 'summary')
            if issue is not None:
                return "[%s](https://jira.nuxeo.com/browse/%s): %s" % (key, key, issue.fields.summary)
        return "[%s](https://jira.nuxeo.com/browse/%s)" % (key, key)

    @property
    def activate(self):
        return self.config('active', False)

    @property
    def whitelisted_private_repositories(self):
        return self.configlist('whitelisted_private_repositories', [])

    def handle_repository(self, organization, name, private):
        if not private:
            return True
        key = "%s/%s" % (organization, name)
        return key in self.whitelisted_private_repositories
