import logging

import socket
from logmatic import LogmaticHandler, JsonFormatter

from nxtools.hooks.tests import HooksTestCase


# class LogServiceTest(HooksTestCase):
#
#     def testLogmatic(self):
#         logger = logging.getLogger('nxtools.hooks.tests.test_log.LogServiceTest')
#         logger.setLevel(logging.INFO)
#
#         logmatic = LogmaticHandler('')
#
#         formatter = JsonFormatter(fmt="%(asctime) %(name) %(processName) %(filename)  %(funcName) %(levelname) %(lineno) %(module) %(threadName) %(message)",
#                                  datefmt="%Y-%m-%dT%H:%M:%SZ%z",
#                                   extra={
#                                       'type': 'captain-hooks',
#                                       'tags': ['captain-hooks'],
#                                       'host': socket.gethostname()
#                                   })
#
#         logmatic.setFormatter(formatter)
#         logger.addHandler(logmatic)
#
#         logger.info('This is a test message')
