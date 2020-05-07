@Library("github.com/RedHatInsights/insights-pipeline-lib") _
import groovy.json.JsonSlurper

node {
  // Only run one build at a time; otherwise they'll fail since you can only have one Akamai activation at a time
  properties([disableConcurrentBuilds()])

  stage ("create backup for old YAML files") {
    APP_NAME = "__APP_NAME__"
    BRANCH = env.BRANCH_NAME.replaceAll("origin/", "")
    if (BRANCH == "prod-stable") {
      PREFIX = ""
      STAGETESTSTR = "\'stage and stable\'"
      PRODTESTSTR = "\'prod and stable\'"
      RELEASESTR = "stable"
      ENVSTR = "prod"
    } else if (BRANCH == "prod-beta") {
      PREFIX = "beta/"
      STAGETESTSTR = "\'stage and beta\'"
      PRODTESTSTR = "\'prod and beta\'"
      RELEASESTR = "beta"
      ENVSTR = "prod"
    } else if (BRANCH == "stage-stable") {
      PREFIX = ""
      STAGETESTSTR = "\'stage and stable\'"
      PRODTESTSTR = "\'prod and stable\'"
      RELEASESTR = "stable"
      ENVSTR = "stage"
    } else if (BRANCH == "stage-beta") {
      PREFIX = "beta/"
      STAGETESTSTR = "\'stage and beta\'"
      PRODTESTSTR = "\'prod and beta\'"
      RELEASESTR = "beta"
      ENVSTR = "stage"
    } else {
      error "Invalid branch name: we only support prod-beta/prod-stable, but we got ${BRANCH}"
    }
    sh "wget -O main.yml.bak https://cloud.redhat.com/${PREFIX}config/main.yml"
    sh "wget -O releases.yml.bak https://cloud.redhat.com/${PREFIX}config/releases.yml"
  }

  stage ("build & activate on Akamai staging") {
    // Use image with python 3.6
    openShiftUtils.withNode(image: "python:3.6-slim") {
      checkout scm
      // cd into akamai folder
      dir("akamai") {
        // Use secret .edgerc file
        withCredentials([
          file(credentialsId: "rhcs-akamai-edgerc", variable: 'EDGERC'),
          string(credentialsId: "rhcs-prod-gateway-secret", variable: 'PRODGATEWAYSECRET'),
          string(credentialsId: "rhcs-pentest-gateway-secret", variable: 'PENTESTGATEWAYSECRET'),
          string(credentialsId: "rhcs-prod-certauth-secret", variable: 'CERTAUTHSECRET')
        ]) {
          sh "set -e"
          sh "rm -rf venv || true"
          sh "python3 -m venv venv"
          sh ". ./venv/bin/activate"
          sh "pip3 install --user -r ./requirements.txt"

          withEnv([
            "PRODGATEWAYSECRET=$PRODGATEWAYSECRET",
            "PENTESTGATEWAYSECRET=$PENTESTGATEWAYSECRET",
            "CERTAUTHSECRET=$CERTAUTHSECRET",
          ]) {
            sh "python3 ./update_api.py $EDGERC STAGING $ENVSTR $BRANCH"
          }

          // Save contents of previousversion.txt as a variable
          PREVIOUSVERSION = readFile('previousversion.txt').trim()
          print("STAGING PREVIOUSVERSION version is v" + PREVIOUSVERSION)
          // Save contents of newversion.txt as a variable
          NEWVERSION = readFile('newversion.txt').trim()
          print("STAGING NEWVERSION version is v" + NEWVERSION)
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
      openShiftUtils.withNode {
        sh "iqe plugin install akamai"
        sh "IQE_AKAMAI_CERTIFI=true DYNACONF_AKAMAI=\'@json {\"release\":\"${RELEASESTR}\"}\' iqe tests plugin akamai -s -m ${STAGETESTSTR}"
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
      openShiftUtils.withNode(image: "python:3.6-slim") {
        checkout scm
        // cd into akamai folder
        dir("akamai") {
          // Use secret .edgerc file
          withCredentials([file(credentialsId: "rhcs-akamai-edgerc", variable: 'EDGERC')]) {
            sh "set -e"
            sh "rm -rf venv || true"
            sh "python3 -m venv venv"
            sh ". ./venv/bin/activate"
            sh "pip3 install --user -r ./requirements.txt"
            sh "python3 ./activate_version.py $EDGERC ${PREVIOUSVERSION} STAGING"
          }
        }
      }
      // If STAGING has errors
      currentBuild.result = 'ABORTED'
      mail body: "Smoke tests failed in Staging. Failed build is here: ${env.BUILD_URL}" ,
            from: 'csc-jenkins@redhat.com',
            replyTo: 'aprice@redhat.com',
            subject: 'CSC build: STAGING smoke tests failed',
            to: 'aprice@redhat.com'
      error('Smoke tests failed in STAGING. Will not activate on PRODUCTION.')
    }
  }

  stage ("activate on akamai production") {
    // Use image with python 3.6
    openShiftUtils.withNode(image: "python:3.6-slim") {
      checkout scm
      // cd into akamai folder
      dir("akamai") {
        // Use secret .edgerc file
        withCredentials([file(credentialsId: "rhcs-akamai-edgerc", variable: 'EDGERC')]) {
          sh "set -e"
          sh "rm -rf venv || true"
          sh "python3 -m venv venv"
          sh ". ./venv/bin/activate"
          sh "pip3 install --user -r ./requirements.txt"
          sh "python3 ./activate_version.py $EDGERC ${NEWVERSION} PRODUCTION $ENVSTR true"
          // Save contents of previousversion.txt as a variable
          PREVIOUSVERSION = readFile('previousversion.txt').trim()
          print("PRODUCTION PREVIOUSVERSION is v" + PREVIOUSVERSION)
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

  stage ("run akamai production smoke tests") {
    try {
      openShiftUtils.withNode {
        sh "iqe plugin install akamai"
        sh "IQE_AKAMAI_CERTIFI=true DYNACONF_AKAMAI=\'@json {\"release\":\"${RELEASESTR}\"}\' iqe tests plugin akamai -s -m ${PRODTESTSTR}"
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
      openShiftUtils.withNode(image: "python:3.6-slim") {
        checkout scm
        // cd into akamai folder
        dir("akamai") {
          // Use secret .edgerc file
          withCredentials([file(credentialsId: "rhcs-akamai-edgerc", variable: 'EDGERC')]) {
            sh "set -e"
            sh "rm -rf venv || true"
            sh "python3 -m venv venv"
            sh ". ./venv/bin/activate"
            sh "pip3 install --user -r ./requirements.txt"
            sh "python3 ./activate_version.py $EDGERC ${PREVIOUSVERSION} PRODUCTION"
          }
        }
      }
      // If PRODUCTION has errors
      currentBuild.result = 'ABORTED'
      mail body: "Smoke tests failed in production. Failed build is here: ${env.BUILD_URL}" ,
            from: 'csc-jenkins@redhat.com',
            replyTo: 'aprice@redhat.com',
            subject: 'CSC build: PROD smoke tests failed',
            to: 'aprice@redhat.com'
      error('Smoke tests failed in PRODUCTION. All changes have been rolled back.')
    }
  }
}
