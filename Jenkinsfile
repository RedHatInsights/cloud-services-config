@Library("github.com/RedHatInsights/insights-pipeline-lib") _
import groovy.json.JsonSlurper

node {
  stage ("deploy") {
    openShift.withNode(image: "docker-registry.default.svc:5000/jenkins/jenkins-slave-base-centos7-python36:latest") {
      checkout scm
      sh "cd akamai"
      sh "set -e"
      sh "pip install -r ./requirements.txt"
      sh "python ./update_api.py"
    }
  }
}
