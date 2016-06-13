import unittest

from mock.mock import Mock
from nxtools import services
from nxtools.hooks.services.config import Config


class HooksTestCase(unittest.TestCase):

    def setUp(self):
        super(HooksTestCase, self).setUp()

        services.add(Config('nxtools/hooks/tests/resources/config.ini'))

    def tearDown(self):
        super(HooksTestCase, self).tearDown()

        services.reload()


class TestMocks(object):

    def __init__(self):
        self.__dict__["_items"] = {}

    def __getattr__(self, item):
        if item not in self._items:
            self._items[item] = Mock()
        return self._items[item]
