@Library("github.com/RedHatInsights/insights-pipeline-lib") _
import groovy.json.JsonSlurper

node {
  stage ("activate on staging") {
    // Use image with python 3.6
    openShift.withNode(image: "docker-registry.default.svc:5000/jenkins/jenkins-slave-base-centos7-python36:latest") {
      checkout scm
      // cd into akamai folder
      dir("akamai") {
        // Use secret .edgerc file
        withCredentials([file(credentialsId: "rhcs-akamai-edgerc", variable: 'EDGERC')]) {
          sh "set -e"
          sh "rm -rf venv || true"
          sh "python3 -m venv venv"
          sh "source ./venv/bin/activate"
          sh "pip3 install --user -r ./requirements.txt"
          sh "python3 ./update_api.py $EDGERC"
        }
      }
    }
  }
  stage ("run akamai staging smoke tests") {
    openShift.withNode(image: "docker-registry.default.svc:5000/jenkins/jenkins-slave-base-centos7-python36:latest") {
      git url: 'https://github.com/RedHatInsights/akamai-smoke-test.git',
        credentialsId: 'jenkins-qa-bot',
        branch: 'master'
      sh "git pull origin master"
      sh "sh run_stage.sh"
    }
  }
}
