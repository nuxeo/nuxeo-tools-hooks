from mongoengine.document import Document
from mongoengine.fields import StringField, IntField


class StoredPullRequest(Document):
    branch = StringField()
    repository = StringField()
    head_commit = StringField()
    pull_number = IntField()
