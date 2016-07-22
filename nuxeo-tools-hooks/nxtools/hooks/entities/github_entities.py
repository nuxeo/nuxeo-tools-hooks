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

from github.CommitStatus import CommitStatus as BaseCommitStatus
from github.GithubObject import NotSet, NonCompletableGithubObject
from github.NamedUser import NamedUser
from github.Organization import Organization
from github.PaginatedList import PaginatedList
from github.PullRequest import PullRequest
from github.Repository import Repository


class PushEvent(NonCompletableGithubObject):
    """
    This class represents PushEvent.
    The reference can be found here https://developer.github.com/v3/activity/events/types/#pushevent
    """

    @property
    def ref(self):
        return self._ref.value

    @property
    def before(self):
        return self._before.value

    @property
    def after(self):
        return self._after.value

    @property
    def created(self):
        return self._created.value

    @property
    def deleted(self):
        return self._deleted.value

    @property
    def forced(self):
        return self._forced.value

    @property
    def base_ref(self):
        return self._base_ref.value

    @property
    def compare(self):
        return self._compare.value

    @property
    def commits(self):
        return self._commits.value

    @property
    def head_commit(self):
        """
        :rtype: nxtools.hooks.entities.github_entities.Commit
        """
        return self._head_commit.value

    @property
    def repository(self):
        """
        :rtype: github.Repository.Repository
        """
        return self._repository.value

    @property
    def pusher(self):
        """
        :rtype: nxtools.hooks.entities.github_entities.User
        """
        return self._pusher.value

    @property
    def organization(self):
        """
        :rtype: github.Organization.Organization
        """
        return self._organization.value

    @property
    def sender(self):
        """
        :rtype: github.NamedUser.NamedUser
        """
        return self._sender.value

    def _initAttributes(self):
        self._ref = NotSet
        self._before = NotSet
        self._after = NotSet
        self._created = NotSet
        self._deleted = NotSet
        self._forced = NotSet
        self._base_ref = NotSet
        self._compare = NotSet
        self._commits = NotSet
        self._head_commit = NotSet
        self._repository = NotSet
        self._pusher = NotSet
        self._organization = NotSet
        self._sender = NotSet

    def _useAttributes(self, attributes):
        if "ref" in attributes:
            self._ref = self._makeStringAttribute(attributes["ref"])
        if "before" in attributes:
            self._before = self._makeStringAttribute(attributes["before"])
        if "after" in attributes:
            self._after = self._makeStringAttribute(attributes["after"])
        if "created" in attributes:
            self._created = self._makeBoolAttribute(attributes["created"])
        if "deleted" in attributes:
            self._deleted = self._makeBoolAttribute(attributes["deleted"])
        if "forced" in attributes:
            self._forced = self._makeBoolAttribute(attributes["forced"])
        if "base_ref" in attributes:
            self._base_ref = self._makeStringAttribute(attributes["base_ref"])
        if "compare" in attributes:
            self._compare = self._makeStringAttribute(attributes["compare"])
        if "commits" in attributes:
            self._commits = self._makeListOfClassesAttribute(Commit, attributes["commits"])
        if "head_commit" in attributes:
            self._head_commit = self._makeClassAttribute(Commit, attributes["head_commit"])
        if "repository" in attributes:
            self._repository = self._makeClassAttribute(Repository, attributes["repository"])
        if "pusher" in attributes:
            self._pusher = self._makeClassAttribute(User, attributes["pusher"])
        if "organization" in attributes:
            self._organization = self._makeClassAttribute(Organization, attributes["organization"])
        if "sender" in attributes:
            self._sender = self._makeClassAttribute(NamedUser, attributes["sender"])


class PullRequestEvent(NonCompletableGithubObject):

    @property
    def action(self):
        return self._action.value

    @property
    def number(self):
        return self._number.value

    @property
    def pull_request(self):
        """
        :rtype: github.PullRequest.PullRequest
        """
        return self._pull_request.value

    @property
    def repository(self):
        """
        :rtype: github.Repository.Repository
        """
        return self._repository.value

    @property
    def organization(self):
        """
        :rtype: github.Organization.Organization
        """
        return self._organization.value

    @property
    def sender(self):
        """
        :rtype: github.NamedUser.NamedUser
        """
        return self._sender.value

    def _initAttributes(self):
        self._action = NotSet
        self._number = NotSet
        self._pull_request = NotSet
        self._repository = NotSet
        self._organization = NotSet
        self._sender = NotSet
        
    def _useAttributes(self, attributes):
        if "action" in attributes:
            self._action = self._makeStringAttribute(attributes["action"])
        if "number" in attributes:
            self._number = self._makeIntAttribute(attributes["number"])
        if "pull_request" in attributes:
            self._pull_request = self._makeClassAttribute(PullRequest,  attributes["pull_request"])
        if "repository" in attributes:
            self._repository = self._makeClassAttribute(Repository, attributes["repository"])
        if "organization" in attributes:
            self._organization = self._makeClassAttribute(Organization, attributes["organization"])
        if "sender" in attributes:
            self._sender = self._makeClassAttribute(NamedUser, attributes["sender"])


class Commit(NonCompletableGithubObject):

    @property
    def id(self):
        return self._id.value

    @property
    def tree_id(self):
        return self._tree_id.value

    @property
    def distinct(self):
        return self._distinct.value

    @property
    def message(self):
        return self._message.value

    @property
    def timestamp(self):
        return self._timestamp.value

    @property
    def url(self):
        return self._url.value

    @property
    def author(self):
        return self._author.value

    @property
    def committer(self):
        return self._committer.value

    @property
    def added(self):
        return self._added.value

    @property
    def removed(self):
        return self._removed.value

    @property
    def modified(self):
        return self._modified.value

    def _initAttributes(self):
        self._id = NotSet
        self._tree_id = NotSet
        self._distinct = NotSet
        self._message = NotSet
        self._timestamp = NotSet
        self._url = NotSet
        self._author = NotSet
        self._committer = NotSet
        self._added = NotSet
        self._removed = NotSet
        self._modified = NotSet

    def _useAttributes(self, attributes):
        if "id" in attributes:
            self._id = self._makeStringAttribute(attributes["id"])
        if "tree_id" in attributes:
            self._tree_id = self._makeStringAttribute(attributes["tree_id"])
        if "distinct" in attributes:
            self._distinct = self._makeBoolAttribute(attributes["distinct"])
        if "message" in attributes:
            self._message = self._makeStringAttribute(attributes["message"])
        if "timestamp" in attributes:
            self._timestamp = self._makeDatetimeAttribute(attributes["timestamp"])
        if "url" in attributes:
            self._url = self._makeStringAttribute(attributes["url"])
        if "author" in attributes:
            self._author = self._makeClassAttribute(Author, attributes["author"])
        if "committer" in attributes:
            self._committer = self._makeClassAttribute(Author, attributes["committer"])
        if "added" in attributes:
            self._added = self._makeListOfStringsAttribute(attributes["added"])
        if "removed" in attributes:
            self._removed = self._makeListOfStringsAttribute(attributes["removed"])
        if "modified" in attributes:
            self._modified = self._makeListOfStringsAttribute(attributes["modified"])


class User(NonCompletableGithubObject):

    @property
    def name(self):
        return self._name.value

    @property
    def email(self):
        return self._email.value

    def _initAttributes(self):
        self._name = NotSet
        self._email = NotSet

    def _useAttributes(self, attributes):
        if "name" in attributes:
            self._name = self._makeStringAttribute(attributes["name"])
        if "email" in attributes:
            self._email = self._makeStringAttribute(attributes["email"])


class Author(User):

    @property
    def c(self):
        return self._username.value

    def _initAttributes(self):
        User._initAttributes(self)
        self._username = NotSet

    def _useAttributes(self, attributes):
        User._useAttributes(self, attributes)
        if "username" in attributes:
            self._username = self._makeStringAttribute(attributes["username"])


class GithubEntityWrapper(object):
    def __init__(self, wrappee):
        self.__dict__["_wrappee"] = wrappee

    def __getattr__(self, name):
        return getattr(self._wrappee, name)

    def __setattr__(self, name, value):
        setattr(self._wrappee, name, value)


class OrganizationWrapper(GithubEntityWrapper):

    def get_repo(self, name):
        """
        :rtype: nxtools.hooks.entities.github_entities.RepositoryWrapper
        """
        assert isinstance(name, (str, unicode)), name
        return RepositoryWrapper(self._wrappee.get_repo(name))


class RepositoryWrapper(GithubEntityWrapper):

    GITHUB_DIFF_ACCEPT_HEADER = {"Accept": "application/vnd.github.diff"}

    def get_commit_diff(self, sha):
        assert isinstance(sha, (str, unicode)), sha

        headers, body = self._requester.requestJsonAndCheck("GET", self._wrappee.url + "/commits/" + sha, None,
                                           RepositoryWrapper.GITHUB_DIFF_ACCEPT_HEADER, None)

        return unicode(body['data'])

    def get_commit(self, sha):
        assert isinstance(sha, (str, unicode)), sha

        return CommitWrapper(self._wrappee.get_commit(sha))


class CommitWrapper(GithubEntityWrapper):

    def get_statuses(self):
        """
        :calls: `GET /repos/:owner/:repo/commits/:ref/statuses <http://developer.github.com/v3/repos/statuses>`_
        :rtype: github.PaginatedList.PaginatedList
        """
        return PaginatedList(
            CommitStatus,
            self._requester,
            self.url + "/statuses",
            None
        )


class CommitStatus(BaseCommitStatus):

    def __init__(self, requester, headers, attributes, completed):
        super(CommitStatus, self).__init__(requester, headers, attributes, completed)

    @property
    def context(self):
        return self._context.value

    def _initAttributes(self):
        self._context = NotSet
        super(CommitStatus, self)._initAttributes()

    def _useAttributes(self, attributes):
        if "context" in attributes:
            self._context = self._makeStringAttribute(attributes["context"])
        super(CommitStatus, self)._useAttributes(attributes)
