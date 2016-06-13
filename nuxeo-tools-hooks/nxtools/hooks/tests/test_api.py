from nxtools import services
from nxtools.hooks.services.database import DatabaseService
from nxtools.hooks.tests import HooksTestCase


class ApiTest(HooksTestCase):

    def setUp(self):
        super(ApiTest, self).setUp()

        services.get(DatabaseService).connect()

    def test_something(self):
        json = "{\"name\": \"pgm\"}"
