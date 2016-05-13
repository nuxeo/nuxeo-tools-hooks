import unittest

from mock.mock import Mock, patch


class TestMocks(object):

    def __init__(self):
        self.__dict__["_items"] = {}

    def __getattr__(self, item):
        if item not in self._items:
            self._items[item] = Mock()
        return self._items[item]


class HooksTestCase(unittest.TestCase):

    def setUp(self):
        self.mocks = TestMocks()