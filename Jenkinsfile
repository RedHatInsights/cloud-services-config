@Library("github.com/RedHatInsights/insights-pipeline-lib") _
import groovy.json.JsonSlurper

node {
  stage ("deploy") {
    openShift.withNode(image: "docker-registry.default.svc:5000/jenkins/python27-jenkins-slave:latest") {
      checkout scm
      sh "akamai/run_dev.sh"
    }
  }
}
