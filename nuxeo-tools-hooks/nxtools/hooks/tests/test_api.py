import unittest

from mongoengine.document import Document
from nxtools import services
from nxtools.hooks.services.database import DatabaseService


class ApiTest(unittest.TestCase):

    def setUp(self):
        super(ApiTest, self).setUp()

        services.get(DatabaseService).connect()

    def test_something(self):
        json = "{\"name\": \"pgm\"}"
