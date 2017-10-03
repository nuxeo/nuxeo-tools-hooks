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

from github.Commit import Commit
from nxtools import ServiceContainer, services
from nxtools.hooks.endpoints.webhook.github_handlers import AbstractGithubJsonHandler
from nxtools.hooks.endpoints.webhook.github_hook import GithubHook
from nxtools.hooks.entities.db_entities import PullRequestReview, StoredPullRequest
from nxtools.hooks.entities.github_entities import PullRequestEvent, IssueCommentEvent
from nxtools.hooks.services.github_service import GithubService, GithubReviewService

log = logging.getLogger(__name__)


@ServiceContainer.service
class GithubStorePullRequestHandler(AbstractGithubJsonHandler):

    MSG_OK = "OK"

    def can_handle(self, headers, body):
        return "pull_request" == headers[GithubHook.payloadHeader]

    def _do_handle(self, payload_body):
        log.info('GithubStorePullRequestHandler.handle')
        event = PullRequestEvent(None, None, payload_body, True)

        stored_pull_request = self.store_pull_request(event)

        self.trigger_review(stored_pull_request, event)

        return 200, GithubStorePullRequestHandler.MSG_OK

    @staticmethod
    def trigger_review(stored_pr, event):
        """
        :type stored_pr: nxtools.hooks.entities.db_entities.StoredPullRequest
        :type event: PullRequestEvent
        :return:
        """
        review_service = services.get(GithubReviewService)  # type: GithubReviewService
        log.debug('Review active: %s, Repository private: %s', review_service.activate, event.repository.private)
        if review_service.activate and event.repository.private is False:
            repository = services.get(GithubService).get_organization(event.organization.login) \
                .get_repo(event.repository.name)
            stored_pr.gh_object = repository.get_pull(stored_pr.pull_number)
            last_commit = stored_pr.gh_object.get_commits().reversed[0]  # type: Commit

            log.debug('PullRequestEvent action: %s', event.action)
            log.info('Review asked for %s/%s/pull/%d/commits/%s',
                     stored_pr.organization, stored_pr.repository, stored_pr.pull_number, last_commit.sha)

            if stored_pr.review is None:
                stored_pr.review = PullRequestReview(pull_request=stored_pr)
            review = stored_pr.review

            if event.action in ['opened', 'synchronize']:
                review_service.set_review_status(repository, last_commit, 0, review_service.pending_status)

            if event.action == 'opened':
                review.owners = review_service.get_owners(event)

                slack_resp = review_service.slack_notify(stored_pr, review.owners, force_create=True)
                github_comment = review_service.github_notify(stored_pr, review.owners)

                review.slack_id = slack_resp.get('ts', None)
                review.comment_id = github_comment.id

            try:
                review.save()
                stored_pr.save()
            except Exception, e:
                log.warn('Error while saving PR review: %s', e.message)
                raise e

    @staticmethod
    def store_pull_request(event):
        return services.get(GithubService).create_pullrequest(event.organization, event.repository, event.pull_request)


@ServiceContainer.service
class GithubReviewCommentHandler(AbstractGithubJsonHandler):

    def can_handle(self, headers, body):
        return "issue_comment" == headers[GithubHook.payloadHeader]

    def _do_handle(self, payload_body):
        log.info('GithubReviewCommentHandler.handle')
        event = IssueCommentEvent(None, None, payload_body, True)
        service = services.get(GithubReviewService)  # type: GithubReviewService

        log.debug('Review active: %s, Repository private: %s', service.activate, event.repository.private)
        if service.activate and event.repository.private is False:

            log.debug('Comment body: "%s"', event.comment.body)
            if event.comment.body.strip() in service.mark_reviewed_comment or \
                    ('changes' in event.raw_data
                     and event.raw_data['changes']['body']['from'].strip() in service.mark_reviewed_comment):
                repository = services.get(GithubService).get_organization(event.organization.login) \
                    .get_repo(event.repository.name)

                pr = StoredPullRequest.objects(
                    organization=event.organization.login,
                    repository=event.repository.name,
                    pull_number=event.issue.number
                ).first()  # type: StoredPullRequest

                pr.gh_object = repository.get_pull(pr.pull_number)

                last_commit = pr.gh_object.get_commits().reversed[0]  # type: Commit
                log.info('Got review for %s/%s/pull/%d/commits/%s',
                         event.organization.login, event.repository.name, event.issue.number, last_commit.sha)

                reviewers = service.get_reviewers(pr)
                pr.review.update(add_to_set__owners=reviewers)

                status = service.success_status if len(reviewers) >= service.required_reviews else service.pending_status

                service.set_review_status(repository, last_commit, len(reviewers), status)
                service.slack_notify(pr, reviewers, status, len(reviewers), reviewers)

        return 200, 'OK'
