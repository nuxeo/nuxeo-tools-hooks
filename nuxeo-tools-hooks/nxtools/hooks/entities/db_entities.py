from mongoengine.document import Document
from mongoengine.fields import StringField, IntField, DateTimeField


class StoredPullRequest(Document):
    branch = StringField()
    organization = StringField()
    repository = StringField()
    head_commit = StringField()
    pull_number = IntField()
    created_at = DateTimeField()
