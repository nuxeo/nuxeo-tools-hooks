import json

from flask.blueprints import Blueprint
from flask_cors.extension import CORS
from nxtools import ServiceContainer, services
from nxtools.hooks.endpoints import AbstractEndpoint
from nxtools.hooks.entities.db_entities import StoredPullRequest
from nxtools.hooks.services import BootableService
from nxtools.hooks.services.github_service import GithubService
from nxtools.hooks.services.jira_service import JiraService
from nxtools.hooks.services.oauth_service import OAuthService


@ServiceContainer.service
class ApiEndpoint(AbstractEndpoint, BootableService):

    __blueprint = Blueprint('api', __name__)

    def boot(self, app):
        """ :type app: nxtools.hooks.app.ToolsHooksApp """

        CORS(ApiEndpoint.blueprint(), **services.get(ApiEndpoint).get_cors_config())
        app.flask.register_blueprint(ApiEndpoint.blueprint(), url_prefix="/api")

    @staticmethod
    def blueprint():
        return ApiEndpoint.__blueprint

    @staticmethod
    @__blueprint.route('/services')
    @OAuthService.secured
    def services():
        return json.dumps([t.__module__ + "." + t.__name__ for t, n, v in services.list(object)])

    @staticmethod
    @__blueprint.route('/validate/<code>')
    def validate(code):
        return services.get(OAuthService).validate(code)

    @staticmethod
    @__blueprint.route('/me')
    @OAuthService.secured
    def me():
        if services.get(OAuthService).authenticated:
            return 'OK', 200
        else:
            return 'KO', 401

    @staticmethod
    @__blueprint.route('/pull_requests')
    @OAuthService.secured
    def list_pull_requests():
        github = services.get(GithubService)  # type: GithubService
        jira = services.get(JiraService)  # type: JiraService
        pullrequests = []

        for stored_pr in StoredPullRequest.objects():
            organization = github.get_organization(stored_pr.organization)
            repository = organization.get_repo(stored_pr.repository)
            pullrequest = repository.get_pull(stored_pr.pull_number)
            head_commit = repository.get_commit(pullrequest.head.sha)
            jira_key = jira.get_issue_id_from_branch(pullrequest.head.ref)
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

        return json.dumps(pullrequests)

    def get_cors_config(self):
        return {k.replace("cors_", ""): v for k, v in self.config.items(self.config_section, {
            "cors_origins": "*",
            "cors_supports_credentials": True
        }).iteritems() if k.startswith("cors_")}
