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

import logging
import operator
import re

from github.Commit import Commit
from github.File import File
from github.IssueComment import IssueComment
from github.PullRequest import PullRequest
from nxtools import ServiceContainer, services
from nxtools.hooks.endpoints.webhook.github_handlers import AbstractGithubJsonHandler
from nxtools.hooks.endpoints.webhook.github_hook import AbstractGithubHandler, GithubHook
from nxtools.hooks.entities.github_entities import PullRequestEvent, RepositoryWrapper, IssueCommentEvent
from nxtools.hooks.services import AbstractService
from nxtools.hooks.services.github_service import GithubService
from slackclient import SlackClient

log = logging.getLogger(__name__)


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
        currentAuthor = 'none'
        lines = []

        for match in re.findall(r'(<img alt="@([^"]+)" class="avatar blame-commit-avatar"|<td class="blame-commit-info")',
                                blame, re.M):
            if match[1]:
                currentAuthor = match[1]
            else:
                lines.append(currentAuthor)

        return lines

    def get_owners(self, event):
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

    def count_reviews(self, pull_request, last_commit):
        """
         :type pull_request: PullRequest
         :type last_commit: Commit
         """
        reviews = 0
        for comment in pull_request.get_issue_comments():  # type: IssueComment
            if comment.created_at > last_commit.commit.author.date and \
                            comment.body.strip() in self.mark_reviewed_comment and \
                            self.has_required_organizations(comment.user.login):
                reviews += 1

        return reviews

    def set_review_status(self, repository, pull_request, last_commit):
        """
         :type repository: github.Repository.Repository
         :type pull_request: github.PullRequest.PullRequest
         :type last_commit: github.Commit.Commit
         """
        reviews_count = self.count_reviews(pull_request, last_commit)

        status = self.success_status if reviews_count >= self.required_reviews else self.pending_status
        description = '%d (of %d) reviews' % (reviews_count, self.required_reviews)

        log.info('Setting status of %s/%s/commits/%s to: %s',
                 repository.organization.login,
                 repository.name,
                 last_commit.sha,
                 description)

        last_commit.create_status(
            status,
            description=description,
            context=self.review_context)

    def slack_notify(self, event, owners):
        reviewers = " ".join(["@" + o for o in owners])
        slack = SlackClient(self.slack_token)

        log.info('Sending slack notification for %s/%s/pull/%d in %s',
                 event.organization.login, event.repository.name, event.pull_request.number, self.slack_channel)

        slack.api_call('chat.postMessage',
                       channel=self.slack_channel,
                       username=self.slack_username,
                       icon_emoji=self.slack_icon,
                       unfurl_links=False,
                       attachments=[
                           {
                               "fallback": "%s (%s) has created %s/%s PR #%d: %s" % (
                                   event.pull_request.user.login,
                                   event.pull_request.user.html_url,
                                   event.organization.login,
                                   event.repository.name,
                                   event.pull_request.number,
                                   event.pull_request.title,
                               ),
                               "color": "good",
                               "author_name": event.pull_request.user.login,
                               "author_link": event.pull_request.user.html_url,
                               "title": "%s/%s PR #%d: %s" % (
                                   event.organization.login,
                                   event.repository.name,
                                   event.pull_request.number,
                                   event.pull_request.title),
                               "title_link": event.pull_request.html_url,
                               "text": "Needs 2 review to merge."
                           }
                       ])

    def github_comment(self, event, owners):
        reviewers = ", ".join(["@" + o for o in owners])

        repository = services.get(GithubService).get_organization(event.organization.login). \
            get_repo(event.repository.name)  # type: RepositoryWrapper

        pull_request = repository.get_pull(event.pull_request.number)  # type: PullRequest

        log.info('Notifying potential reviewers with a comment on %s/%s/pull/%d',
                 event.organization.login, event.repository.name, event.pull_request.number, self.slack_channel)

        pull_request.create_issue_comment("From the blame information on this pull request, potential reviewers: "
                                          + reviewers)

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


@ServiceContainer.service
class GithubReviewNotifyHandler(AbstractGithubJsonHandler):

    def can_handle(self, headers, body):
        return "pull_request" == headers[GithubHook.payloadHeader]

    def _do_handle(self, payload_body):
        log.info('GithubReviewNotifyHandler.handle')
        event = PullRequestEvent(None, None, payload_body, True)
        review_service = services.get(GithubReviewService)  # type: GithubReviewService

        log.debug('Review active: %s, Repository private: %s', review_service.activate, event.repository.private)
        if review_service.activate and event.repository.private is False:
            repository = services.get(GithubService).get_organization(event.organization.login) \
                .get_repo(event.repository.name)
            pull_request = repository.get_pull(event.pull_request.number)  # type: PullRequest
            last_commit = pull_request.get_commits().reversed[0]  # type: Commit

            log.debug('PullRequestEvent action: %s', event.action)
            log.info('Review asked for %s/%s/pull/%d/commits/%s',
                     event.organization.login, event.repository.name, event.pull_request.number, last_commit.sha)

            if event.action in ['opened', 'synchronize']:
                review_service.set_review_status(repository, pull_request, last_commit)

            if event.action == 'opened':
                # owners = review_service.get_owners(event)
                owners = []
                review_service.slack_notify(event, owners)
                # review_service.github_comment(event, owners)

        return 200, 'OK'


@ServiceContainer.service
class GithubReviewCommentHandler(AbstractGithubJsonHandler):

    def can_handle(self, headers, body):
        return "issue_comment" == headers[GithubHook.payloadHeader]

    def _do_handle(self, payload_body):
        log.info('GithubReviewCommentHandler.handle')
        event = IssueCommentEvent(None, None, payload_body, True)
        review_service = services.get(GithubReviewService)  # type: GithubReviewService

        log.debug('Review active: %s, Repository private: %s', review_service.activate, event.repository.private)
        if review_service.activate and event.repository.private is False:

            log.debug('Comment body: "%s"', event.comment.body)
            if event.comment.body.strip() in review_service.mark_reviewed_comment or \
                    ('changes' in event.raw_data
                        and event.raw_data['changes']['body']['from'].strip() in review_service.mark_reviewed_comment):
                repository = services.get(GithubService).get_organization(event.organization.login)\
                    .get_repo(event.repository.name)
                pr = repository.get_pull(event.issue.number)  # type: PullRequest
                last_commit = pr.get_commits().reversed[0]  # type: Commit
                log.info('Got review for %s/%s/pull/%d/commits/%s',
                          event.organization.login, event.repository.name, event.issue.number, last_commit.sha)

                review_service.set_review_status(repository, pr, last_commit)

        return 200, 'OK'
