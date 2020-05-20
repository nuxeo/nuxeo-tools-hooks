
/*
 * (C) Copyright 2016-2019 Nuxeo SA (http://nuxeo.com/) and contributors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * you may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Contributors:
 *     Pierre-Gildas MILLON <pgmillon@nuxeo.com>, jcarsique
 */

node('SLAVE') {
    timeout(time: 60, unit: 'MINUTES') {
        timestamps {
            try {
                def sha
                stage 'prepare'
                checkout scm
                sha = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
                sh '''#!/bin/bash -ex
rm -rf venv
virtualenv venv
source venv/bin/activate
pip install -r dev-requirements.txt
pip install -e .
'''
                stage 'test'
                sh '''#!/bin/bash -ex
source venv/bin/activate
nosetests
'''
                stage 'build'
                sh '''#!/bin/bash -ex
source venv/bin/activate
python setup.py sdist
'''
                image = docker.build 'nuxeo/nuxeo-tools-hooks'
                sh """#!/bin/bash -ex
docker tag ${image.id} dockerpriv.nuxeo.com:443/nuxeo/nuxeo-tools-hooks:${env.BRANCH_NAME}
docker push dockerpriv.nuxeo.com:443/nuxeo/nuxeo-tools-hooks:${env.BRANCH_NAME}
docker tag ${image.id} dockerpriv.nuxeo.com:443/nuxeo/nuxeo-tools-hooks:${sha}
docker push dockerpriv.nuxeo.com:443/nuxeo/nuxeo-tools-hooks:${sha}
"""
                logstash_image = docker.build('nuxeo/nuxeo-tools-hooks-logstash', 'docker/logstash')
                sh """#!/bin/bash -ex
docker tag ${logstash_image.id} dockerpriv.nuxeo.com:443/nuxeo/nuxeo-tools-hooks-logstash:${env.BRANCH_NAME}
docker push dockerpriv.nuxeo.com:443/nuxeo/nuxeo-tools-hooks-logstash:${env.BRANCH_NAME}
"""
                archiveArtifacts allowEmptyArchive: true, artifacts: 'dist/*.tar.gz', fingerprint: true, onlyIfSuccessful: true
                jiraIssueSelector(issueSelector: [$class: 'DefaultIssueSelector'])

                if('master' == env.BRANCH_NAME) {
                    build job: '/Private/System/deploy-hooks.nuxeo.org', parameters: [
                            [$class: 'StringParameterValue', name: 'DASHBOARD_PACKAGE', value: 'https://qa.nuxeo.org/jenkins/job/Misc/job/nuxeo-tools-qa-dashboard/lastSuccessfulBuild/artifact/nuxeo-tools-qa-dashboard.zip'],
                            [$class: 'StringParameterValue', name: 'TOOLS_BRANCH', value: 'master'],
                            [$class: 'StringParameterValue', name: 'ANSIBLE_PRIV_BRANCH', value: '$TOOLS_BRANCH']
                    ], wait: false
                }
            } catch (e) {
                currentBuild.result = "FAILURE"
                step([$class: 'ClaimPublisher'])
                throw e
            } finally {
                // Update revelant Jira issues only if we are working on the master branch
                if (env.BRANCH_NAME == 'master') {
                    step([$class: 'JiraIssueUpdater',
                        issueSelector: [$class: 'DefaultIssueSelector'],
                        scm: scm])
                }
            }
        }
    }
}

