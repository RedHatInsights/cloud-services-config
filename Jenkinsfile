@Library("github.com/RedHatInsights/insights-pipeline-lib") _
import groovy.json.JsonSlurper

node {
  stage ("deploy") {
    openShift.withNode(image: "docker-registry.default.svc:5000/jenkins/python27-jenkins-slave:latest") {
      checkout scm
      sh "set -e && (rm -rf venv || true) && python3 -m venv venv && source venv/bin/activate && pip install -r akamai/requirements.txt && akamai/python update_api.py"
    }
  }
}
