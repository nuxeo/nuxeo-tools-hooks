
/*
 * (C) Copyright 2016 Nuxeo SA (http://nuxeo.com/) and contributors.
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
 *     Pierre-Gildas MILLON <pgmillon@nuxeo.com>
 */

node('SLAVE') {
    try {
        stage 'prepare'
        step([$class: 'GitHubCommitStatusSetter', contextSource: [$class: 'ManuallyEnteredCommitContextSource', context: 'ci/qa.nuxeo.com'], statusResultSource: [$class: 'ConditionalStatusResultSource', results: [[$class: 'AnyBuildResult', message: 'Building on Nuxeo CI', state: 'PENDING']]]])

        checkout scm
        sh "git rev-parse --short HEAD > .git/commit-id"
        commit_id = readFile('.git/commit-id')

        sh '''#!/bin/bash -ex
rm -rf venv
virtualenv venv
'''
        stage 'build'
        sh '''#!/bin/bash -ex
source venv/bin/activate
pip install -r dev-requirements.txt
pip install -e .
'''
        stage 'test'
        sh '''#!/bin/bash -ex
source venv/bin/activate
nosetests
'''
        stage 'package'
        sh '''#!/bin/bash -ex
source venv/bin/activate
python setup.py sdist'''

        image = docker.build 'nuxeo/nuxeo-tools-hooks'

        sh "docker tag ${image.id} dockerpriv.nuxeo.com:443/nuxeo/nuxeo-tools-hooks:${env.BRANCH_NAME}"
        sh "docker push dockerpriv.nuxeo.com:443/nuxeo/nuxeo-tools-hooks:${env.BRANCH_NAME}"

        sh "docker tag ${image.id} dockerpriv.nuxeo.com:443/nuxeo/nuxeo-tools-hooks:${commit_id}"
        sh "docker push dockerpriv.nuxeo.com:443/nuxeo/nuxeo-tools-hooks:${commit_id}"

        step([$class: 'ArtifactArchiver', allowEmptyArchive: true, artifacts: 'dist/*.tar.gz', excludes: null, fingerprint: true, onlyIfSuccessful: true])
        step([$class: 'JiraIssueUpdater', issueSelector: [$class: 'DefaultIssueSelector'], scm: scm])
        step([$class: 'GitHubCommitStatusSetter', contextSource: [$class: 'ManuallyEnteredCommitContextSource', context: 'ci/qa.nuxeo.com'], statusResultSource: [$class: 'ConditionalStatusResultSource', results: [[$class: 'AnyBuildResult', message: 'Building on Nuxeo CI', state: 'SUCCESS']]]])

        if('master' == env.BRANCH_NAME) {
            build job: '/Private/System/deploy-hooks.nuxeo.org', parameters: [
                    [$class: 'StringParameterValue', name: 'DASHBOARD_PACKAGE', value: 'https://qa.nuxeo.org/jenkins/job/Misc/job/nuxeo-tools-qa-dashboard/lastSuccessfulBuild/artifact/nuxeo-tools-qa-dashboard.zip'],
                    [$class: 'StringParameterValue', name: 'TOOLS_BRANCH', value: 'master'],
                    [$class: 'StringParameterValue', name: 'ANSIBLE_PRIV_BRANCH', value: '$TOOLS_BRANCH']
            ], wait: false
        }

        if('SUCCESS' != currentBuild.getPreviousBuild().getResult()) {
            slackSend channel: '#devops-notifs', color: 'good', message: "${env.JOB_NAME} - #${env.BUILD_NUMBER} Back to normal (<${env.BUILD_URL}|Open>)", teamDomain: 'nuxeo', token: 'u6jxyUxDz7imQindMfJcsZXf'
        }
    } catch (e) {
        step([$class: 'GitHubCommitStatusSetter', contextSource: [$class: 'ManuallyEnteredCommitContextSource', context: 'ci/qa.nuxeo.com'], statusResultSource: [$class: 'ConditionalStatusResultSource', results: [[$class: 'AnyBuildResult', message: 'Building on Nuxeo CI', state: 'FAILURE']]]])
        if('FAILURE' != currentBuild.getPreviousBuild().getResult()) {
            slackSend channel: '#devops-notifs', color: 'danger', message: "${env.JOB_NAME} - #${env.BUILD_NUMBER} Failure (<${env.BUILD_URL}|Open>)", teamDomain: 'nuxeo', token: 'u6jxyUxDz7imQindMfJcsZXf'
        }
        throw e
    }
}
