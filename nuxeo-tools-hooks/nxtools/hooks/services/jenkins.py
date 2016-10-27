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
from jenkinsapi.jenkins import Jenkins
from nxtools import ServiceContainer
from nxtools.hooks.services import AbstractService

log = logging.getLogger(__name__)


@ServiceContainer.service
class JenkinsService(AbstractService):

    __instances = {}

    def instance_config(self, instance_id, key, default=None):
        return self.config('instance_%s_%s' % (instance_id, key), self.config('default_' + key, default))

    def _get_instance(self, instance_id):
        """
        :param instance_id:
        :rtype: Jenkins
        """
        if instance_id not in self.__instances:
            url = self.instance_config(instance_id, 'url')
            username = self.instance_config(instance_id, 'username')

            log.info('Creating new Jenkins instance: %s - %s@%s', instance_id, username, url)
            self.__instances[instance_id] = Jenkins(
                url,
                username,
                self.instance_config(instance_id, 'password', self.instance_config(instance_id, 'token')),
            lazy=True)
        return self.__instances[instance_id]

    # def trigger_job(self, instance_id, job_id, parameters=None):
    #     log.info('Triggering %s/job/%s/params=%s', instance_id, job_id, parameters)
    #     self._get_instance(instance_id).build_job(job_id, parameters)

    def trigger_webhook(self, instance_id, webhook_url, payload, headers=None):
        log.info('Triggering hook %s%s', instance_id, webhook_url)
        instance = self._get_instance(instance_id)

        instance.requester.post_and_confirm_status(
            instance.base_server_url() + webhook_url,
            data=payload,
            headers=dict({
                'Content-Type': 'application/json'
                         }.items() + headers.items() if headers else [])
        )
