import json

from flask.blueprints import Blueprint
from nxtools import ServiceContainer, services
from nxtools.hooks.endpoints import AbstractEndpoint
from nxtools.hooks.entities.api_entities import ViewObjectWrapper
from nxtools.hooks.entities.db_entities import StoredPullRequest
from nxtools.hooks.services.github_service import GithubService
from nxtools.hooks.services.json_encoders import APIPullRequestJSONEncoder


@ServiceContainer.service
class ApiEndpoint(AbstractEndpoint):

    __blueprint = Blueprint('api', __name__)

    @staticmethod
    def blueprint():
        return ApiEndpoint.__blueprint

    @staticmethod
    @__blueprint.route('/services',)
    def services():
        return json.dumps([t.__module__ + "." + t.__name__ for t, n, v in services.list(object)])

    @staticmethod
    @__blueprint.route('/pull_requests',)
    def list_pull_requests():
        github = services.get(GithubService)  # type: GithubService
        pullrequests = []

        for pr in StoredPullRequest.objects():
            organization = github.get_organization(pr.organization)
            repository = organization.get_repo(pr.repository)
            pullrequests.append(ViewObjectWrapper(repository.get_pull(pr.pull_number), pr))

        return json.dumps(pullrequests, cls=APIPullRequestJSONEncoder)

    def get_cors_config(self):
        return {k: v for k, v in self.config.items(self.config_section, {
            "cors_origins": "*"
        }).iteritems() if k.startswith("cors_")}
