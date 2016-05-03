from nxtools.hooks.webhook.github_hook import InvalidPayloadException, AbstractGithubHandler


class GithubReviewHandler(AbstractGithubHandler):

    markReviewedComments = [":+1:"]

    @property
    def organization(self):
        """
        :rtype github.Organization.Organization
        """
        return self.hook.organization

    def handle(self, payload_body):
        try:
            comment_body = payload_body["comment"]["body"].strip()
            repository_name = payload_body["repository"]["name"]
            issue_id = payload_body["issue"]["number"]

            if comment_body in GithubReviewHandler.markReviewedComments:
                repository = self.organization.get_repo(repository_name)
                pr = repository.get_pull(issue_id)
                last_commit = pr.get_commits().reversed[0]

                for status in last_commit.get_statuses():
                    if status.raw_data["context"] == "review/nuxeo" and status.state == "success":
                        return

                print("reviewed")

        except KeyError, e:
            raise InvalidPayloadException(e)