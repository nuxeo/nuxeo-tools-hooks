from nxtools.hooks.endpoints.webhook.github_hook import InvalidPayloadException, AbstractGithubHandler


class GithubReviewHandler(AbstractGithubHandler):

    markReviewedComments = [":+1:"]

    def handle(self, payload_body):
        try:
            comment_body = payload_body["comment"]["body"].strip()
            repository_name = payload_body["repository"]["name"]
            issue_id = payload_body["issue"]["number"]
            organization = payload_body["organization"]["login"]

            if comment_body in GithubReviewHandler.markReviewedComments:
                repository = self.hook.get_organization(organization).get_repo(repository_name)
                pr = repository.get_pull(issue_id)
                last_commit = pr.get_commits().reversed[0]

                for status in last_commit.get_statuses():
                    if status.raw_data["context"] == "review/nuxeo" and status.state == "success":
                        return

                print("reviewed")

        except KeyError, e:
            raise InvalidPayloadException(e)