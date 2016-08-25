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

import unittest

import os

import flask
from mock.mock import Mock, patch
from nxtools import services
from nxtools.hooks.services.config import Config
from nxtools.hooks.services.github_service import NoSuchOrganizationException


class HooksTestCase(unittest.TestCase):

    @property
    def app(self):
        return flask.Flask(__name__)

    def setUp(self):
        super(HooksTestCase, self).setUp()

        self.mocks = TestMocks()

        def get_organization(name):
            if 'nuxeo' == name:
                return self.mocks.organization
            raise NoSuchOrganizationException(name)

        self.mocks.organization.login = 'nuxeo'
        patcher_organization = patch('github.MainClass.Github.get_organization', side_effect=get_organization)
        patcher_organization.start()

        self.addCleanup(patcher_organization.stop)

        os.environ[Config.ENV_PREFIX + Config.CONFIG_FILE_KEY] = 'nxtools/hooks/tests/resources/config.ini'
        services.get(Config).reload()

    def tearDown(self):
        super(HooksTestCase, self).tearDown()

        services.reload()
        self.mocks.clear()


class TestMocks(object):

    def __init__(self):
        self.__dict__["_items"] = {}

    def __getattr__(self, item):
        if item not in self._items:
            self._items[item] = Mock()
        return self._items[item]

    def clear(self):
        self.__dict__["_items"] = {}
