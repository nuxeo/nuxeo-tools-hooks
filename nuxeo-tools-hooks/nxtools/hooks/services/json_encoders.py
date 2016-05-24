from json.encoder import JSONEncoder

from nxtools.hooks.entities.api_entities import ViewObjectWrapper


class APIPullRequestJSONEncoder(JSONEncoder):

    def default(self, o):
        if isinstance(o, ViewObjectWrapper):
            return {
                'organization': o.organization,
                'repository': o.repository,
                'additions': o.additions,
                'assignee': o.assignee.login if o.assignee else None,
                'base': o.base.ref,
                'body': o.body,
                'changed_files': o.changed_files,
                'closed_at': o.closed_at.isoformat() if o.closed_at else None,
                'comments': o.comments,
                'comments_url': o.comments_url,
                'commits': o.commits,
                'commits_url': o.commits_url,
                'created_at': o.created_at.isoformat(),
                'deletions': o.deletions,
                'diff_url': o.diff_url,
                'head': o.head.ref,
                'html_url': o.html_url,
                'id': o.id,
                'issue_url': o.issue_url,
                'merge_commit_sha': o.merge_commit_sha,
                'mergeable': o.mergeable,
                'mergeable_state': o.mergeable_state,
                'merged': o.merged,
                'merged_at': o.merged_at.isoformat() if o.merged_at else None,
                'merged_by': o.merged_by.login,
                'milestone': o.milestone.id if o.milestone else None,
                'number': o.number,
                'patch_url': o.patch_url,
                'review_comment_url': o.review_comment_url,
                'review_comments': o.review_comments,
                'state': o.state,
                'title': o.title,
                'updated_at': o.updated_at.isoformat() if o.updated_at else None,
                'url': o.url,
                'user': o.user.login
            }
        else:
            return super(APIPullRequestJSONEncoder, self).default(o)
