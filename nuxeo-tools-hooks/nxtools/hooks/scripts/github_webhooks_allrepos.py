#!/usr/bin/env python
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
import os
import logging
import sys

from github.MainClass import Github
from github.Organization import Organization
from nxtools.hooks.client import CaptainHooksClient

"""
This scripts is used to setup webhooks on all Nuxeo Github repositories
"""

logging.basicConfig(level=logging.INFO)


class GithubWebHooksAllRepos:

    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    ORGANIZATION = 'nuxeo'

    def __init__(self):
        self.client = CaptainHooksClient()
        pass

    def run(self):
        if self.GITHUB_TOKEN is None:
            logging.critical('No github OAuth token defined in the GITHUB_TOKEN env variable')
            sys.exit(1)

        github = Github(self.GITHUB_TOKEN)
        logging.info('Fetching organization %s', self.ORGANIZATION)
        orga = github.get_organization(self.ORGANIZATION)  # type: Organization
        logging.info('Fetching organization repositories')
        for repo in orga.get_repos():
            pass

if __name__ == '__main__':
    GithubWebHooksAllRepos().run()
