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

import json
from github.Hook import Hook
from github.MainClass import Github
from github.Organization import Organization
from github.Repository import Repository
from nxtools.hooks.client import CaptainHooksClient, CaptainHooksClientException

"""
This scripts is used to setup webhooks on all Nuxeo GitHub repositories
"""

logging.basicConfig(level=logging.INFO, filename='logs/GithubWebHooksAllRepos.log')


class GithubWebHooksAllRepos:

    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    ORGANIZATION = 'nuxeo'

    def __init__(self):
        pass

    def run(self):
        if self.GITHUB_TOKEN is None:
            logging.critical('No GitHub OAuth token defined in the GITHUB_TOKEN env variable')
            sys.exit(1)

        github = Github(self.GITHUB_TOKEN)
        captain_hooks = CaptainHooksClient(self.GITHUB_TOKEN)

        logging.info('Fetching organization %s', self.ORGANIZATION)
        orga = github.get_organization(self.ORGANIZATION)  # type: Organization
        logging.info('Fetching organization repositories')
        for repo in orga.get_repos():  # type: Repository
            for hook in repo.get_hooks():  # type: Hook
                logging.info('%s/%s:backup: ' + json.dumps(hook.raw_data), orga.login, repo.name)
            logging.info('%s/%s:updating', orga.login, repo.name)
            try:
                captain_hooks.setup_webhooks(orga.login, repo.name, {
                    'absent': [
                        {'url': 'http://qapreprod.in.nuxeo.com/jenkins/github-webhook/'},
                        {'url': 'https://qa.nuxeo.org/githooks/send-email'},
                    ],
                    'present': [
                        {
                            'name': 'web',
                            'config': {
                                'content_type': 'json',
                                'url': 'https://hooks.nuxeo.org/hook/'
                            },
                            'events': ['push', 'pull_request'],
                            'active': True
                        },
                    ]
                })
                logging.info('%s/%s:done', orga.login, repo.name)
            except CaptainHooksClientException, e:
                logging.warn('%s/%s:failed: %s', orga.login, repo.name, e)

if __name__ == '__main__':
    GithubWebHooksAllRepos().run()
