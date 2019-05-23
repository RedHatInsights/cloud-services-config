@Library("github.com/RedHatInsights/insights-pipeline-lib") _
import groovy.json.JsonSlurper

node {
  stage ("deploy") {
    // 
    openShift.withNode(image: "docker-registry.default.svc:5000/jenkins/jenkins-slave-base-centos7-python36:latest") {
      withCredentials([file(credentialsId: "rhcs-akamai-edgerc", variable: 'EDGERC')]) {
        checkout scm
        sh "set -e"
        sh "cd akamai"
        sh "rm -rf venv || true"
        sh "python3 -m venv venv"
        sh "source ./venv/bin/activate"
        sh "pip3 install --user -r ./requirements.txt"
        sh "python3 ./update_api.py $EDGERC"
      }
    }
  }
}
