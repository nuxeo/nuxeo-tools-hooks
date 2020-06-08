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

class Email:

    def __init__(self, sender, to, reply_to, subject, body):
        self._sender = sender
        self._to = to
        self._reply_to = reply_to
        self._subject = subject
        self._body = body

    @property
    def body(self):
        return self._body

    @property
    def subject(self):
        return self._subject

    @property
    def sender(self):
        return self._sender

    @property
    def to(self):
        if isinstance(self._to, list):
            return ", ".join(self._to)
        return self._to

    @property
    def reply_to(self):
        return self._reply_to
