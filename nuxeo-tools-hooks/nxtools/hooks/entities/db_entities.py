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

from datetime import datetime
from mongoengine import CASCADE
from mongoengine.document import Document
from mongoengine.fields import StringField, IntField, DateTimeField, ReferenceField, LongField

log = logging.getLogger(__name__)


class StoredPullRequest(Document):
    branch = StringField()
    organization = StringField()
    repository = StringField()
    head_commit = StringField()
    pull_number = IntField()
    created_at = DateTimeField()
    updated_at = DateTimeField()
    review = ReferenceField('PullRequestReview')  # type: PullRequestReview

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

        res = super(StoredPullRequest, self).save(*args, **kwargs)
        log.info('Pull request %s/%s/pull/%d saved', self.organization, self.repository, self.pull_number)

        return res


class PullRequestReview(Document):
    pull_request = ReferenceField(StoredPullRequest, reverse_delete_rule=CASCADE)  # type: StoredPullRequest
    slack_id = StringField()
    comment_id = LongField()
    created_at = DateTimeField()
    updated_at = DateTimeField()

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

        res = super(PullRequestReview, self).save(*args, **kwargs)
        log.info('Review saved for %s/%s/pull/%d saved',
                 self.pull_request.organization, self.pull_request.repository, self.pull_request.pull_number)
        return res
