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
import logging
import re

from nxtools import services, ServiceContainer
from nxtools.hooks.endpoints.webhook.github_handlers import AbstractGithubHandler
from nxtools.hooks.endpoints.webhook.github_hook import GithubHook
from nxtools.hooks.services.jenkins import JenkinsService
from requests.packages.urllib3.exceptions import HTTPError

log = logging.getLogger(__name__)


@ServiceContainer.service
class GithubJenkinsTriggerHandler(AbstractGithubHandler):

    DEFAULT_GITHUB_URL = '/github-webhook/'

    def can_handle(self, headers, body):
        return "push" == headers[GithubHook.payloadHeader]

    @property
    def jenkins_instances(self):
        instances = self.get_config_list('instances', [])
        log.debug('Jenkins instances: %s', instances)
        return instances

    @property
    def jenkins(self):
        """
        :rtype: JenkinsService
        """
        return services.get(JenkinsService)

    def _do_handle(self, payload_body):
        log.info('GithubJenkinsTriggerHandler.handle')
        for instance in self.jenkins_instances:
            log.debug('Forwarding payload to %s', instance)
            try:
                self.jenkins.trigger_webhook(
                    instance,
                    self.get_config('github_webhook_url', self.DEFAULT_GITHUB_URL),
                    payload_body,
                    {
                        GithubHook.payloadHeader: 'push'
                    })
            except Exception, e:
                log.warn("Failed to trigger job on %s: %s", instance, e)
                return 500, 'KO'
        return 200, 'OK'
