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

import paramiko
from github.MainClass import Github
from github.Organization import Organization
from github.Repository import Repository
from github.PullRequest import PullRequest
from paramiko.client import SSHClient
from paramiko.proxy import ProxyCommand
from paramiko.ssh_exception import SSHException

"""
Search reference: https://developer.github.com/v3/search/
"""

logging.basicConfig(level=logging.INFO)


class GithubNuxeocomPRCleanup:

    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    SSH_PKEY = os.getenv('SSH_KEY')
    PREVIEW_DOMAIN = os.getenv('PREVIEW_DOMAIN')
    BASTION_IP = os.getenv('BASTION_IP')

    def __init__(self):
        pass

    def run(self):
        if self.GITHUB_TOKEN is None:
            logging.critical('No github OAuth token defined in the GITHUB_TOKEN env variable')
            sys.exit(1)
        if self.SSH_PKEY is None:
            logging.critical('SSH_KEY not configured, please set it to you private SSH key file')
            sys.exit(1)

        github = Github(self.GITHUB_TOKEN)
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.SSH_PKEY = os.path.expanduser(self.SSH_PKEY)

        orga = github.get_organization('nuxeo')  # type: Organization
        repo = orga.get_repo('nuxeo.com')  # type: Repository
        opened_pulls = [('/var/www/nuxeo.com/pr-%d.' % pull.number) + self.PREVIEW_DOMAIN for pull in repo.get_pulls()]

        try:
            proxy = ProxyCommand(('ssh -i %s -W 10.10.0.63:22 ' % self.SSH_PKEY) + self.BASTION_IP)
            ssh.connect('10.10.0.63', username='root', sock=proxy, key_filename=self.SSH_PKEY)
            _, stdout, _ = ssh.exec_command('ls -d /var/www/nuxeo.com/pr-*')
            [ssh.exec_command('rm -rf ' + line.strip()) for line in stdout.readlines() if line.strip() not in opened_pulls]
            ssh.close()
        except SSHException, e:
            logging.critical('Could work on remote: %s', e)
            sys.exit(1)


if __name__ == '__main__':
    GithubNuxeocomPRCleanup().run()
