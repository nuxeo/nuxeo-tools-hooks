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

import logmatic
import re

import socket

from nxtools import services
from nxtools.hooks.services.config import Config


class JsonFormatter(logmatic.JsonFormatter):

    def config(self, key, default=None):
        return services.get(Config).get(Config.get_section(self), key, default)

    def configlist(self, key, default=None):
        return services.get(Config).getlist(Config.get_section(self), key, default)

    @property
    def entry_type(self):
        return self.config('type', 'nxtools-hooks')

    @property
    def entry_tags(self):
        return self.configlist('tags', [])

    def __init__(self,
                 fmt="%(asctime) %(name) %(processName) %(filename)  %(funcName) %(levelname) %(lineno) %(module) %(threadName) %(message)",
                 datefmt="%Y-%m-%dT%H:%M:%SZ%z", *args, **kwargs):

        super(JsonFormatter, self).__init__(fmt, datefmt, {
            'type': self.entry_type,
            'tags': self.entry_tags,
            'host': socket.gethostname()
        }, *args, **kwargs)

