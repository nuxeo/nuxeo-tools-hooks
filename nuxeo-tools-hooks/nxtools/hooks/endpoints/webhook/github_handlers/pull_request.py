"""
(C) Copyright 2016-2020 Nuxeo SA (http://nuxeo.com/) and contributors.

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
    Anahide Tchertchian <at@nuxeo.com>
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
        activate = review_service.activate
        orga_name = event.organization.login
        repo_name = event.repository.name
        private = event.repository.private
        log.debug("Review active: %s, Repository organization: '%s', name: '%s', private: %s",
                  activate, orga_name, repo_name, private)
        if activate and review_service.handle_repository(orga_name, repo_name, private):
            repository = services.get(GithubService).get_organization(orga_name).get_repo(repo_name)
            stored_pr.gh_object = repository.get_pull(stored_pr.pull_number)

            log.debug('PullRequestEvent action: %s', event.action)
            log.info('Review asked for %s/%s/pull/%d',
                     stored_pr.organization, stored_pr.repository, stored_pr.pull_number)

            if stored_pr.review is None:
                stored_pr.review = PullRequestReview(pull_request=stored_pr)
            review = stored_pr.review

            if event.action == 'opened':
                github_comment = review_service.github_notify(stored_pr)
                if github_comment:
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

