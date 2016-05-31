import unittest

from nxtools import services
from nxtools.hooks.tests import TestMocks


class HooksTestCase(unittest.TestCase):

    def setUp(self):
        self.mocks = TestMocks()

    def tearDown(self):
        services.reload()
