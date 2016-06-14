from nxtools.hooks.tests import TestMocks, HooksTestCase


class WebHooksTestCase(HooksTestCase):

    def setUp(self):
        super(WebHooksTestCase, self).setUp()

        self.mocks = TestMocks()
