# -*- coding: utf-8 -*-
import json

from mock.mock import Mock
from nxtools.hooks.entities.github_entities import PushEvent
from nxtools.hooks.entities.github_entities import RepositoryWrapper
from nxtools.hooks.tests.handlers.test_github import GithubHandlerTest
from nxtools.hooks.endpoints.github_handlers.push_notify_mail import GithubPushNotifyMailHandler


class GithubNotifyMailHandlerTest(GithubHandlerTest):

    def __init__(self, methodName='runTest'):
        super(GithubNotifyMailHandlerTest, self).__init__(methodName)

        self._email_service = None

    def setUp(self):
        super(GithubNotifyMailHandlerTest, self).setUp()
        self._handler = GithubPushNotifyMailHandler(self.hook, self.email_service)

    def get_event_from_body(self, body):
        """
        :rtype: nxtools.hooks.entities.github_entities.PushEvent
        """
        return PushEvent(None, None, body, True)

    @property
    def handler(self):
        """
        :rtype: nxtools.hooks.endpoints.github_handlers.push_notify_mail.GithubPushNotifyMailHandler
        """
        return self._handler

    @property
    def email_service(self):
        if not self._email_service:
            self._email_service = Mock()
        return self._email_service

    def test_bad_branch_payload(self):
        with GithubHandlerTest.payload_file('github_push') as payload:
            body = self.get_json_body_from_payload(payload)

            self.assertTrue(body["ref"])
            body["ref"] = "refs/wrong/anything"

            self.assertTrue(self.handler.is_bad_ref(self.get_event_from_body(body)))
            self.assertTupleEqual((400, GithubPushNotifyMailHandler.MSG_BAD_REF % body["ref"]),
                                  self.handler.handle(body))
            self.email_service.sendemail.assert_not_called()

    def test_ignored_stable_branch_payload(self):
        with GithubHandlerTest.payload_file('github_push') as payload:
            body = self.get_json_body_from_payload(payload)
            self.handler.hook.config._config.set(self.handler.config_section, "ignored_branches", "stable")
            self.handler.hook.config._config.set(self.handler.config_section, "ignore_checks",
                                                 "nxtools.hooks.endpoints.github_handlers.push_notify_mail."
                                                 "branch_ignore")

            self.assertTrue(body["ref"])
            body["ref"] = "refs/heads/stable"

            event = self.get_event_from_body(body)
            branch = event.ref[11:]
            self.assertTupleEqual((False, True, None), self.handler.check_branch_ignored(event))
            self.assertTupleEqual((200, GithubPushNotifyMailHandler.MSG_OK), self.handler.handle(body))
            self.email_service.sendemail.assert_called_once()

            self.assertFalse(self.handler.is_jenkins(event))
            email = self.handler.get_commit_email(event, event.commits[0], True)
            self.assertRegexpMatches(email.body, 'WARNING: only Jenkins should commit on this branch')
            self.assertRegexpMatches(email.body, 'Branch: ' + branch)
            self.assertRegexpMatches(email.subject, '^\[WARN\] %s: %s \(branch@%s\)$' % (
                event.repository.name,
                event.commits[0].message,
                branch))

    def test_ignored_snapshot_branch_payload(self):
        with GithubHandlerTest.payload_file('github_push') as payload:
            body = self.get_json_body_from_payload(payload)
            self.handler.hook.config._config.set(self.handler.config_section, "ignored_branch_suffixes", "-SNAPSHOT")
            self.handler.hook.config._config.set(self.handler.config_section, "ignore_checks",
                                                 "nxtools.hooks.endpoints.github_handlers.push_notify_mail."
                                                 "suffix_ignore")

            self.assertTrue(body["ref"])
            body["ref"] = "refs/heads/5.7-SNAPSHOT"

            event = self.get_event_from_body(body)
            branch = event.ref[11:]
            self.assertTupleEqual((False, True, None), self.handler.check_branch_ignored(event))
            self.assertTupleEqual((200, GithubPushNotifyMailHandler.MSG_OK), self.handler.handle(body))
            self.email_service.sendemail.assert_called_once()
            self.assertFalse(self.handler.is_jenkins(event))

            email = self.handler.get_commit_email(event, event.commits[0], True)
            self.assertRegexpMatches(email.body, 'WARNING: only Jenkins should commit on this branch')
            self.assertRegexpMatches(email.body, 'Branch: ' + branch)
            self.assertRegexpMatches(email.subject, '^\[WARN\] %s: %s \(branch@%s\)$' % (
                event.repository.name,
                event.commits[0].message,
                branch))

    def test_jenkins_ignored_payload(self):
        with GithubHandlerTest.payload_file('github_push') as payload:
            body = self.get_json_body_from_payload(payload)
            self.handler.hook.config._config.set(self.handler.config_section, "ignored_branches", "stable")

            self.assertTrue(body["ref"])
            self.assertTrue(body["pusher"])
            body["ref"] = "refs/heads/stable"
            body["pusher"] = {
                "name": self.handler.jenkins_username,
                "email": self.handler.jenkins_email,
            }

            event = self.get_event_from_body(body)
            response = GithubPushNotifyMailHandler.MSG_IGNORE_BRANCH % event.ref[11:]
            self.assertTupleEqual((True, False, response), self.handler.check_branch_ignored(event))
            self.assertTupleEqual((200, response), self.handler.handle(body))
            self.email_service.sendemail.assert_not_called()
            self.assertTrue(self.handler.is_jenkins(event))

    def test_jenkins_payload(self):
        with GithubHandlerTest.payload_file('github_push') as payload:
            body = self.get_json_body_from_payload(payload)

            self.assertTrue(body["pusher"])
            body["pusher"] = {
                "name": self.handler.jenkins_username,
                "email": self.handler.jenkins_email,
            }

            event = self.get_event_from_body(body)
            branch = event.ref[11:]
            self.assertTupleEqual((False, False, None), self.handler.check_branch_ignored(event))
            self.assertTupleEqual((200, GithubPushNotifyMailHandler.MSG_OK), self.handler.handle(body))
            self.email_service.sendemail.assert_called_once()

            email = self.handler.get_commit_email(event, event.commits[0], False)
            self.assertEqual(email.sender, "Pierre-Gildas MILLON via Jenkins <%s>" % self.handler.sender)
            self.assertEqual(email.reply_to, "Pierre-Gildas MILLON via Jenkins <pgmillon@nuxeo.com>")
            self.assertRegexpMatches(email.body, 'Branch: ' + branch)
            self.assertRegexpMatches(email.body, 'Author: Pierre-Gildas MILLON via Jenkins <pgmillon@nuxeo.com>')
            self.assertRegexpMatches(email.body, 'Pusher: %s <%s>' % (
                self.handler.jenkins_username,
                self.handler.jenkins_email
            ))
            self.assertRegexpMatches(email.subject, '^%s: %s \(branch@%s\)$' % (
                event.repository.name,
                event.commits[0].message,
                branch))

    def test_jenkins_payload_via_jenkins(self):
        with GithubHandlerTest.payload_file('github_push') as payload:
            body = self.get_json_body_from_payload(payload)

            self.assertTrue(body["pusher"])
            body["pusher"] = {
                "name": self.handler.jenkins_username,
                "email": self.handler.jenkins_email,
            }

            self.assertTrue(body["commits"][0]["author"])
            self.assertTrue(body["commits"][0]["committer"])
            body["commits"][0]["author"] = {
                "name": self.handler.jenkins_name,
                "email": self.handler.jenkins_email,
                "username": self.handler.jenkins_username
            }
            body["commits"][0]["committer"] = body["commits"][0]["author"]

            event = self.get_event_from_body(body)
            self.assertTupleEqual((False, False, None), self.handler.check_branch_ignored(event))
            self.assertTupleEqual((200, GithubPushNotifyMailHandler.MSG_OK), self.handler.handle(body))
            self.email_service.sendemail.assert_called_once()

            email = self.handler.get_commit_email(event, event.commits[0], False)
            self.assertEqual(email.sender, "%s <%s>" % (self.handler.jenkins_name, self.handler.sender))
            self.assertEqual(email.reply_to, "%s <%s>" % (self.handler.jenkins_name, self.handler.jenkins_email))
            self.assertRegexpMatches(email.body, 'Branch: ' + event.ref[11:])
            self.assertRegexpMatches(email.body, 'Author: Jenkins Nuxeo <jenkins@nuxeo.com>')

    def test_payload_with_accents(self):
        with GithubHandlerTest.payload_file('github_push') as payload:
            body = self.get_json_body_from_payload(payload)

            self.assertTrue(body["commits"][0])
            body["commits"][0]["message"] += u" héhé"
            body["commits"][0]["committer"]["name"] += u" héhé"

            event = PushEvent(None, None, body, True)
            self.assertFalse(self.handler.is_bad_ref(event))
            self.assertTupleEqual((False, False, None), self.handler.check_branch_ignored(event))
            self.assertTupleEqual((200, GithubPushNotifyMailHandler.MSG_OK), self.handler.handle(body))
            self.email_service.sendemail.assert_called_once()

            email = self.handler.get_commit_email(event, event.commits[0], False)
            self.assertEqual(email.sender, "Pierre-Gildas MILLON hehe <noreply@nuxeo.com>")
            self.assertEqual(email.reply_to, "Pierre-Gildas MILLON hehe <pgmillon@nuxeo.com>")
            self.assertEqual(email.subject, "%s: %s (branch@%s)" % (
                event.repository.name,
                "NXBT-1074: better comments hehe",
                event.ref[11:]))

    def test_private_repository(self):
        with GithubHandlerTest.payload_file('github_push') as payload:
            body = self.get_json_body_from_payload(payload)

            self.assertTrue(body["repository"])
            body["repository"]["private"] = True

            event = PushEvent(None, None, body, True)
            email = self.handler.get_commit_email(event, event.commits[0], False)
            self.assertEqual(email.to, "interne-checkins@lists.nuxeo.com")

    def test_diff_retriever(self):
        with GithubHandlerTest.payload_file('github_push') as payload:
            body = self.get_json_body_from_payload(payload)

            event = PushEvent(None, None, body, True)

            self.mocks.requester.requestJson.side_effect = Exception
            self.assertTupleEqual((200, GithubPushNotifyMailHandler.MSG_OK), self.handler.handle(body))
            self.email_service.sendemail.assert_called_once()

            email = self.handler.get_commit_email(event, event.commits[0], False)
            self.assertRegexpMatches(email.body, 'Could not read diff - see %s.diff for raw diff' %
                                     event.commits[0].url)

    def test_jira_regexp(self):
        with GithubHandlerTest.payload_file('github_push') as payload:
            body = self.get_json_body_from_payload(payload)

            self.assertTrue(body["commits"][0])
            body["commits"][0]["message"] = "check regexp for NXP-8238 and nxp-666 and also NXS-1234 as well as " \
                                            "NXCONNECT-1234"

            event = PushEvent(None, None, body, True)
            self.assertTupleEqual((False, False, None), self.handler.check_branch_ignored(event))
            self.assertTupleEqual((200, GithubPushNotifyMailHandler.MSG_OK), self.handler.handle(body))
            self.email_service.sendemail.assert_called_once()

            email = self.handler.get_commit_email(event, event.commits[0], False)
            self.assertRegexpMatches(email.body, 'JIRA: https://jira.nuxeo.com/browse/NXP-8238')
            self.assertRegexpMatches(email.body, 'JIRA: https://jira.nuxeo.com/browse/NXP-666')
            self.assertRegexpMatches(email.body, 'JIRA: https://jira.nuxeo.com/browse/NXS-1234')
            self.assertRegexpMatches(email.body, 'JIRA: https://jira.nuxeo.com/browse/NXS-1234')

    def test_jenkins_payload_with_ignore(self):
        with GithubHandlerTest.payload_file('github_push') as payload:
            body = self.get_json_body_from_payload(payload)
            self.handler.hook.config._config.set(self.handler.config_section, "ignored_repositories",
                                                 "qapriv.nuxeo.org-conf")
            self.handler.hook.config._config.set(self.handler.config_section, "ignore_checks",
                                                 "nxtools.hooks.endpoints.github_handlers.push_notify_mail."
                                                 "repository_ignore")

            event = PushEvent(None, None, body, True)

            self.assertTupleEqual((False, False, None), self.handler.check_branch_ignored(event))
            self.assertTupleEqual((200, GithubPushNotifyMailHandler.MSG_OK), self.handler.handle(body))
            self.email_service.sendemail.assert_called_once()

            self.assertTrue(body["pusher"])
            self.assertTrue(body["commits"][0])
            self.assertTrue(body["repository"])
            body["commits"].append(body["commits"][0].copy())
            body["commits"][0]["message"] = "NXP-8238: updated by SYSTEM."
            body["commits"][1]["message"] = "NXP-8238: yo"
            body["repository"]["name"] = "qapriv.nuxeo.org-conf"
            body["pusher"] = {
                "name": self.handler.jenkins_username,
                "email": self.handler.jenkins_email,
            }

            event = PushEvent(None, None, body, True)

            self.assertTupleEqual((False, False, None), self.handler.check_branch_ignored(event))

            body["commits"][1]["message"] = "NXP-8238: updated by SYSTEM."
            event = PushEvent(None, None, body, True)

            response = GithubPushNotifyMailHandler.MSG_IGNORE_COMMITS % ", ".join([
                event.commits[0].url, event.commits[1].url
            ])
            self.assertTupleEqual((True, False, response), self.handler.check_branch_ignored(event))
            self.assertTupleEqual((200, response), self.handler.handle(body))
            self.email_service.sendemail.assert_called_once()

    def test_standard_payload(self):
        with GithubHandlerTest.payload_file('github_push') as payload:
            body = self.get_json_body_from_payload(payload)

            self.assertTrue(body["commits"][0])
            event = PushEvent(None, None, body, True)

            self.assertTupleEqual((False, False, None), self.handler.check_branch_ignored(event))

            with open('nxtools/hooks/tests/resources/github_hooks/github_push.commit.diff') as diff_file, \
                    open('nxtools/hooks/tests/resources/github_hooks/github_push.email.txt') as email_file:
                self.mocks.requester.requestJson.return_value = diff_file.read()
                self.mocks.repository_url.return_value = event.repository.url

                self.assertTupleEqual((200, GithubPushNotifyMailHandler.MSG_OK), self.handler.handle(body))
                self.email_service.sendemail.assert_called_once()

                email = self.handler.get_commit_email(event, event.commits[0], False)

                self.assertMultiLineEqual(email_file.read(), email.body)
                self.assertEqual(email.to, "ecm-checkins@lists.nuxeo.com")
                self.mocks.requester.requestJson.assert_called_with("GET", event.commits[0].url, None,
                                                                    RepositoryWrapper.GITHUB_DIFF_ACCEPT_HEADER, None)
