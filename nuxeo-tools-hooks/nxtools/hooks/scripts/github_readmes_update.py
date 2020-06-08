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

from github.ContentFile import ContentFile
from github.MainClass import Github
from github.PaginatedList import PaginatedList
from nxtools.hooks.client import CaptainHooksClient

"""
Search reference: https://developer.github.com/v3/search/
"""

logging.basicConfig(level=logging.INFO)


class GithubReadmesUpdate:

    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

    def __init__(self):
        self.client = CaptainHooksClient()
        pass

    def run(self):
        if self.GITHUB_TOKEN is None:
            logging.critical('No github OAuth token defined in the GITHUB_TOKEN env variable')
            sys.exit(1)

        github = Github(self.GITHUB_TOKEN)
        qualifiers = {
            'query': '',
            'in': 'file',
            'org': 'nuxeo',
            'filename': 'README.md'
        }
        logging.info('Qualifiers: %s', qualifiers)
        search = github.search_code(**qualifiers)  # type: PaginatedList
        logging.info('Number of results: %d', search.totalCount)
        for result in search:  # type: ContentFile
            try:
                logging.info('Updating nuxeo/%s', result.repository.name)
                new_content = result.decoded_content
                commit = result.repository.update_file(
                    '/'+result.path,
                    'NXBT-1198: Remove Company name',
                    new_content,
                    result.sha)['commit']
                logging.info('Updated nuxeo/%s: %s', result.repository.name, commit.html_url)
            except Exception, e:
                logging.warn('Failed failed nuxeo/%s: %s', result.repository.name, e)

if __name__ == '__main__':
    GithubReadmesUpdate().run()
