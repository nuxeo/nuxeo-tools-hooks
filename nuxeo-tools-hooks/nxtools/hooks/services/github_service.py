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

        return stored_pr

    def get_pullrequest(self, stored_pullrequest):
        github = services.get(GithubService)  # type: GithubService
        jira = services.get(JiraService)  # type: JiraService

        try:
            organization = github.get_organization(stored_pullrequest.organization)
            repository = organization.get_repo(stored_pullrequest.repository)
            pullrequest = repository.get_pull(stored_pullrequest.pull_number)
            head_commit = repository.get_commit(pullrequest.head.sha)
            jira_key = jira.get_issue_id_from_branch(stored_pullrequest.branch)
            jira_issue = jira.get_issue(jira_key) if jira_key is not None else None

            if jira_key is None:
                log.info('get_pullrequest: Could not parse JIRA key for %s/%s/pull/%d', organization.login,
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
                'jira_summary': jira_issue.fields.summary if jira_key is not None else None,
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
        for organization_name in re.sub(r"\s+", "", self.config('sync_pullrequests_organizations', ''),
                                        flags=re.UNICODE).split(','):
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
    pending_status = "pending"

    success_status = "success"

    def parse_patch(self, patch):
        deleted_lines = []
        current_from_line = 0

        if patch:
            for line in patch.splitlines():
                if line.startswith('@@'):
                    matches = re.match(r"@@ -([0-9]+),?([0-9]+)? \+([0-9]+),?([0-9]+)? @@", line)
                    if matches is not None:
                        from_line = int(matches.group(1))
                        # from_count = int(matches.group(2))
                        # to_line = int(matches.group(3))
                        # to_count = int(matches.group(4))

                        current_from_line = from_line
                    continue
                if line.startswith('-'):
                    deleted_lines.append(current_from_line)
                if not line.startswith('+'):
                    current_from_line += 1

        return deleted_lines

    def parse_blame(self, blame):
        currentAuthor = None
        lines = []

        try:
            hunks = html5parser.fromstring(blame).xpath('//html:div[contains(@class, "blame-hunk")]',
                                                        namespaces={'html': XHTML_NAMESPACE})
            if not hunks:
                log.warning('No blame hunks found')
            else:
                for hunk_index, hunk in enumerate(hunks):
                    currentAuthor = (hunk.xpath(
                        './/html:a[html:img[contains(@class, "blame-commit-avatar")]]/@aria-label',
                        namespaces={'html': XHTML_NAMESPACE}) or [None])[0]

                    if currentAuthor:
                        log.debug('Hunk #%d author: %s', hunk_index, currentAuthor)
                    else:
                        currentAuthor = 'none'
                        log.warning('Hunk #%d no author found', hunk_index)

                    hunk_lines = hunk.xpath('.//html:div[contains(@class, "blob-num")]/@id',
                                            namespaces={'html': XHTML_NAMESPACE})

                    log.debug('Hunk #%d lines: %s', hunk_index, hunk_lines)

                    if not hunk_lines:
                        log.warning('Hunk #%d no lines found', hunk_index)
                    else:
                        for _ in hunk_lines:
                            lines.append(currentAuthor)
        except LxmlError, e:
            log.warning('Could not parse blame page: %s', e)

        return lines

    def get_owners(self, event):
        """
        :type event: nxtools.hooks.entities.github_entities.PullRequestEvent
        :return:
        """
        files = []
        deletion_owners = {}
        all_owners = {}

        repository = services.get(GithubService).get_organization(event.organization.login). \
            get_repo(event.repository.name)  # type: RepositoryWrapper

        pull_request = repository.get_pull(event.pull_request.number)  # type: PullRequest
        pr_id = '%s/%s/pull/%d' % (event.organization.login, repository.name, pull_request.number)

        log.info('%s: Checking reviewers', pr_id)

        log.debug('%s: Getting & Parsing patch for each files of PR', pr_id)
        for pr_file in pull_request.get_files():  # type: File
            if 'modified' == pr_file.status:
                files.append({'file': pr_file.filename, 'deletions': self.parse_patch(pr_file.patch)})

        files.sort(key=lambda f: len(f['deletions']), reverse=True)
        files = files[:self.number_checked_files]

        for f in files:
            log.debug('%s: %s - %d deletions, getting & parsing blame', pr_id, f['file'], len(f['deletions']))
            blame = self.parse_blame(repository.get_blame(f['file'], event.pull_request.base.sha))

            for name in blame:
                all_owners[name] = all_owners[name] + 1 if name in all_owners else 1

            for line in f['deletions']:
                name = blame[line - 1]
                if name:
                    deletion_owners[name] = deletion_owners[name] + 1 if name in deletion_owners else 1

        authors = [commit.author.login for commit in pull_request.get_commits() if commit.author is not None]
        pr_creator = event.pull_request.user.login

        log.debug('%s: deleted_owners: %s', pr_id, deletion_owners)
        log.debug('%s: all_owners: %s', pr_id, all_owners)

        for owner in deletion_owners:
            if owner in all_owners:
                del all_owners[owner]

        owners = [owner for owner in
                  self.filter_and_sort_owners(deletion_owners, pr_creator, authors)[:1] +
                  self.filter_and_sort_owners(all_owners, pr_creator, authors)]

        return owners[:self.number_reviewers]

    def filter_and_sort_owners(self, owners, pr_creator, authors):
        return [o for o, count in sorted(owners.items(), key=operator.itemgetter(1), reverse=True)
                if o != 'none' and o != pr_creator and o not in authors and self.has_required_organizations(o)]

    def has_required_organizations(self, login):
        github = services.get(GithubService)  # type: GithubService
        return True in [github.get_organization(name).has_in_members(github.get_user(login))
                        for name in self.required_organizations] if self.required_organizations else True

    def get_reviewers(self, pull_request):
        """
         :type pull_request: StoredPullRequest
         """
        reviewers = []
        last_commit = pull_request.gh_object.get_commits().reversed[0]  # type: Commit
        for comment in pull_request.gh_object.get_issue_comments():  # type: IssueComment
            if comment.created_at > last_commit.commit.author.date and \
                            comment.body.strip() in self.mark_reviewed_comment and \
                    self.has_required_organizations(comment.user.login):
                reviewers.append(comment.user.login)

        return reviewers

    def set_review_status(self, repository, last_commit, count, status):
        """
         :type repository: github.Repository.Repository
         :type last_commit: github.Commit.Commit
         :type count: int
         :type status: str
         """
        description = '%d (of %d) reviews' % (count, self.required_reviews)

        log.info('Setting status of %s/%s/commits/%s to: %s',
                 repository.organization.login,
                 repository.name,
                 last_commit.sha,
                 description)

        last_commit.create_status(
            status,
            description=description,
            context=self.review_context)

    def slack_notify(self, pull_request, owners, status=None, reviews_count=0, reviewers=None, force_create=False):
        """
        :type pull_request: nxtools.hooks.entities.db_entities.StoredPullRequest
        :type owners: list
        :type status: str
        :type reviews_count: int
        :type reviewers: list
        :rtype: dict
        """
        reviewers = reviewers if reviewers else []
        suggest_reviewers = ["@" + o for o in owners if o not in reviewers] if owners else []
        slack = SlackClient(self.slack_token)

        log.info('Sending slack notification for %s/%s/pull/%d in %s',
                 pull_request.organization, pull_request.repository, pull_request.gh_object.number, self.slack_channel)

        attachments = {
            'title': "%s/%s PR #%d: %s" % (
                pull_request.organization,
                pull_request.repository,
                pull_request.gh_object.number,
                pull_request.gh_object.title),
            'fallback': "%s (%s) has created %s/%s PR #%d: %s. Potential reviewers: %s" % (
                pull_request.gh_object.user.login,
                pull_request.gh_object.user.html_url,
                pull_request.organization,
                pull_request.repository,
                pull_request.gh_object.number,
                pull_request.gh_object.title,
                ' '.join([o for o in suggest_reviewers])),
            "color": "good",
            "author_name": pull_request.gh_object.user.login,
            "author_link": pull_request.gh_object.user.html_url,
            "title_link": pull_request.gh_object.html_url
        }

        params = {
            'channel': self.slack_channel,
            'username': self.slack_username,
            'unfurl_links': False,
            'as_user': True,
            'attachments': [attachments]
        }

        if not force_create and pull_request.review and pull_request.review.slack_id:
            call = 'chat.update'
            params.update({
                'ts': pull_request.review.slack_id
            })
        else:
            call = 'chat.postMessage'

        parts = []
        if self.pending_status == status:
            parts.append("Needs %d review to merge." % (self.required_reviews - reviews_count))
            if suggest_reviewers:
                parts.append('Potential reviewers: %s.' % ' '.join([o for o in suggest_reviewers]))
        if reviewers:
            text = '%sReviewed by %s.' % ('\n' if parts else '', ', '.join(["@" + o for o in reviewers]))
            parts.append(text)
        elif suggest_reviewers:
            pass

        attachments['text'] = ' '.join(parts)
        resp = slack.api_call(call, **params)

        if not resp.get('ok', False):
            raise SlackException(resp.get('error', 'Unexpected error'))

        return resp

    def github_notify(self, pull_request, owners):
        """
        :type pull_request: nxtools.hooks.entities.db_entities.StoredPullRequest
        :type owners: list
        :rtype: github.IssueComment.IssueComment
        """

        jira_key = services.get(JiraService).get_issue_id_from_branch(pull_request.branch)

        log.info('Notifying potential reviewers with a comment of %s/%s/pull/%d on %s',
                 pull_request.organization, pull_request.repository, pull_request.pull_number, self.slack_channel)

        parts = []
        if owners:
            parts.append("From the blame information on this pull request, potential reviewers: %s" % (
                ", ".join(["@" + o for o in owners])
            ))

        if jira_key:
            parts.append("[View issue in JIRA](https://jira.nuxeo.com/browse/%s)" % jira_key)

        if parts:
            return pull_request.gh_object.create_issue_comment("\n".join(parts))

    @property
    def activate(self):
        return self.config('active', False)

    @property
    def slack_icon(self):
        return self.config('slack_icon', ':nuxeo:')

    @property
    def slack_username(self):
        return self.config('slack_username', 'nuxeo_review')

    @property
    def slack_channel(self):
        return self.config('slack_channel', '#pull-requests')

    @property
    def slack_token(self):
        return self.config('slack_token', '')

    @property
    def number_checked_files(self):
        return self.config('number_checked_files', 5)

    @property
    def number_reviewers(self):
        return self.config('number_reviewers', 3)

    @property
    def mark_reviewed_comment(self):
        allowed_comments = self.config('mark_reviewed_comment', u":+1:,\U0001F44D")
        return re.sub(r"\s+", "", allowed_comments, flags=re.UNICODE).split(",") if allowed_comments else []

    @property
    def required_reviews(self):
        return self.config('required_reviews', 2)

    @property
    def review_context(self):
        return self.config('review_context', 'code-review/nuxeo')

    @property
    def required_organizations(self):
        orgas = self.config('required_organizations', [])
        if orgas:
            orgas = re.sub(r"\s+", "", orgas, flags=re.UNICODE).split(",")
        return orgas
