@Library("github.com/RedHatInsights/insights-pipeline-lib@v1.3") _
import groovy.json.JsonSlurper

node {
  stage ("create backup for old YAML files") {
    String APP_NAME = "__APP_NAME__"
    String BRANCH = env.BRANCH_NAME.replaceAll("origin/", "")
    if (BRANCH == "prod-stable") {
      PREFIX = ""
      TESTSTR = "\'stage and not hashes and not beta\'"
    } else if (BRANCH == "prod-beta") {
      PREFIX = "beta/"
      TESTSTR = "\'stage and not hashes and not stable\'"
    } else {
      error "Invalid branch name: we only support prod-beta/prod-stable, but we got ${BRANCH}"
    }
    sh "wget -O main.yml.bak https://cloud.redhat.com/${PREFIX}config/main.yml"
    sh "wget -O releases.yml.bak https://cloud.redhat.com/${PREFIX}config/releases.yml"
  }

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
          sh "python3 ./update_api.py $EDGERC STAGING"
          // Save contents of previousversion.txt as a variable
          String PREVIOUSVERSION = readFile('previousversion.txt').trim()
        }
      }
    }

    checkout scm
    withCredentials(bindings: [sshUserPrivateKey(credentialsId: "cloud-netstorage",
                  keyFileVariable: "privateKeyFile",
                  passphraseVariable: "",
                  usernameVariable: "")]) {

      AKAMAI_BASE_PATH = "822386"
      AKAMAI_APP_PATH = "/${AKAMAI_BASE_PATH}/${PREFIX}config"

      configFileProvider([configFile(fileId: "9f0c91bc-4feb-4076-9f3e-13da94ff3cef", variable: "AKAMAI_HOST_KEY")]) {
        sh """
          eval `ssh-agent`
          ssh-add \"$privateKeyFile\"
          cp \"$AKAMAI_HOST_KEY\" ~/.ssh/known_hosts
          chmod 600 ~/.ssh/known_hosts
          rsync -arv -e \"ssh -2\" *.yml sshacs@cloud-unprotected.upload.akamai.com:${AKAMAI_APP_PATH}
        """
      }
    }
  }

  stage ("run akamai staging smoke tests") {
    try {
      openShift.withNode(image: "docker-registry.default.svc:5000/jenkins/jenkins-slave-iqe:latest") {
        sh "iqe plugin install akamai"
        sh "IQE_AKAMAI_CERTIFI=true ENV_FOR_DYNACONF=prod iqe tests plugin akamai -s -k ${TESTSTR}"
      }
    } catch(e) {
      // If the tests don't all pass, roll back changes:
      // Re-upload the old main.yml files
      configFileProvider([configFile(fileId: "9f0c91bc-4feb-4076-9f3e-13da94ff3cef", variable: "AKAMAI_HOST_KEY")]) {
        sh "rm main.yml"
        sh "cp main.yml.bak main.yml"
        sh "rm releases.yml"
        sh "cp releases.yml.bak releases.yml"
        withCredentials(bindings: [sshUserPrivateKey(credentialsId: "cloud-netstorage",
                keyFileVariable: "privateKeyFile",
                passphraseVariable: "",
                usernameVariable: "")]) {
          sh """
            eval `ssh-agent`
            ssh-add \"$privateKeyFile\"
            cp \"$AKAMAI_HOST_KEY\" ~/.ssh/known_hosts
            chmod 600 ~/.ssh/known_hosts
            rsync -arv -e \"ssh -2\" *.yml sshacs@cloud-unprotected.upload.akamai.com:${AKAMAI_APP_PATH}
          """
        }
      }
      openShift.withNode(image: "docker-registry.default.svc:5000/jenkins/jenkins-slave-base-centos7-python36:latest") {
        // cd into akamai folder
        dir("akamai") {
          // Use secret .edgerc file
          withCredentials([file(credentialsId: "rhcs-akamai-edgerc", variable: 'EDGERC')]) {
            sh "set -e"
            sh "rm -rf venv || true"
            sh "python3 -m venv venv"
            sh "source ./venv/bin/activate"
            sh "pip3 install --user -r ./requirements.txt"
            // TODO: This isn't coded yet
            sh "python3 ./rollback.py $EDGERC ${PREVIOUSVERSION}"
          }
        }
      }
    }
  }
}
