@Library("github.com/RedHatInsights/insights-pipeline-lib") _
import groovy.json.JsonSlurper

node {
  stage ("deploy") {
    openShift.withNode(image: "docker-registry.default.svc:5000/jenkins/jenkins-slave-base-centos7-python36:latest") {
      checkout scm
      sh "set -e"
      sh "rm -rf venv || true"
      sh "python3 -m venv venv"
      sh "source ./venv/bin/activate"
      sh "pip3 install --user -r ./akamai/requirements.txt"
      sh "python3 ./akamai/update_api.py"
    }
  }
}
