from nxtools import services
from nxtools.hooks.services.config import Config
from nxtools.hooks.tests import TestMocks, HooksTestCase


class WebHooksTestCase(HooksTestCase):

    def setUp(self):
        services.add(Config('nxtools/hooks/tests/resources/config.ini'))
        self.mocks = TestMocks()
