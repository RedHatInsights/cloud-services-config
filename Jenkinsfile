@Library("github.com/RedHatInsights/insights-pipeline-lib") _
import groovy.json.JsonSlurper

node {
  // Only run one build at a time; otherwise they'll fail since you can only have one Akamai activation at a time
  properties([disableConcurrentBuilds()])

  stage ("create backup for old YAML files") {
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
      RELEASESTR = "stable"
      ENVSTR = "stage"
    } else if (BRANCH == "stage-beta") {
      PREFIX = "beta/"
      RELEASESTR = "beta"
      ENVSTR = "stage"
    } else {
      error "Invalid branch name: we only support prod-beta/prod-stable, but we got ${BRANCH}"
    }

    if (ENVSTR == "prod") {
      AKAMAI_APP_PATH = "/822386/${PREFIX}config"
      CSC_CONFIG_PATH = "https://cloud.redhat.com/${PREFIX}config"
      RUN_SMOKE_TESTS = true
    } else {
      AKAMAI_APP_PATH = "/822386/${ENVSTR}/${PREFIX}config"
      CSC_CONFIG_PATH = "https://cloud.redhat.com/${ENVSTR}/${PREFIX}config"
      RUN_SMOKE_TESTS = false   // cannot run smoke tests on stage as it requires vpn
    }

    sh "wget -O main.yml.bak ${CSC_CONFIG_PATH}/main.yml"
    sh "wget -O releases.yml.bak ${CSC_CONFIG_PATH}/releases.yml"
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
          file(credentialsId: "rhcs-$ENVSTR-3scale-origin-json", variable: 'GATEWAYORIGINJSON'),
          file(credentialsId: "rhcs-$ENVSTR-gov-3scale-origin-json", variable: 'FEDRAMPORIGINJSON'),
          file(credentialsId: "rhcs-$ENVSTR-turnpike-origin-json", variable: 'TURNPIKEORIGINJSON'),
          file(credentialsId: "rhcs-openshift-origin-json", variable: 'OPENSHIFTORIGINJSON'),
          file(credentialsId: "rhcs-openshift-mirror-origin-json", variable: 'OPENSHIFTORIGINMIRRORJSON'),
          file(credentialsId: "rhcs-rhorchata-origin-json", variable: 'RHORCHATAORIGINJSON'),
          file(credentialsId: "rhcs-pentest-gateway-origin-json", variable: 'PENTESTGATEWAYORIGINJSON'),
          string(credentialsId: "rhcs-$ENVSTR-gateway-secret", variable: 'GATEWAYSECRET'),
          string(credentialsId: "rhcs-stage-gateway-secret", variable: 'GATEWAYSTAGESECRET'),
          string(credentialsId: "rhcs-pentest-gateway-secret", variable: 'PENTESTGATEWAYSECRET'),
          string(credentialsId: "rhcs-prod-certauth-secret", variable: 'CERTAUTHSECRET')
        ]) {
          sh "set -e"
          sh "rm -rf venv || true"
          sh "python3 -m venv venv"
          sh ". ./venv/bin/activate"
          sh "pip3 install --user -r ./requirements.txt"

          withEnv([
            "GATEWAYSECRET=$GATEWAYSECRET",
            "PENTESTGATEWAYSECRET=$PENTESTGATEWAYSECRET",
            "CERTAUTHSECRET=$CERTAUTHSECRET",
            "EDGERCPATH=$EDGERC",
            "GATEWAYORIGINJSON=$GATEWAYORIGINJSON",
            "TURNPIKEORIGINJSON=$TURNPIKEORIGINJSON"
          ]) {
            sh "python3 ./update_api.py STAGING $ENVSTR $BRANCH"
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
      if (RUN_SMOKE_TESTS) {
        openShiftUtils.withNode {
          withCredentials([
            string(credentialsId: "vaultRoleId", variable: 'DYNACONF_IQE_VAULT_ROLE_ID'),
            string(credentialsId: "vaultSecretId", variable: 'DYNACONF_IQE_VAULT_SECRET_ID'),
          ]) {
            // set some env variables for authentication in the iqe-core pod
            withEnv([
              "DYNACONF_IQE_VAULT_ROLE_ID=$DYNACONF_IQE_VAULT_ROLE_ID",
              "DYNACONF_IQE_VAULT_SECRET_ID=$DYNACONF_IQE_VAULT_SECRET_ID",
              "DYNACONF_IQE_VAULT_LOADER_ENABLED=true",
              "ENV_FOR_DYNACONF=prod"
            ]) {
              // install akamai and 3scale plugins, run smoke tests
              sh "iqe plugin install akamai 3scale"
              sh "IQE_AKAMAI_CERTIFI=true DYNACONF_AKAMAI=\'@json {\"release\":\"${RELEASESTR}\"}\' iqe tests plugin akamai -s -m ${STAGETESTSTR}"
              sh "iqe tests plugin akamai -k 'test_api.py' -m stage"
              sh "iqe tests plugin 3scale --akamai-staging -m akamai_smoke"
            }
          }
        }
      }
      else {
        sh "echo Smoke tests cannot run against STAGE environment as it requires VPN connection"
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
            withEnv([
              "EDGERCPATH=$EDGERC"
            ]) {
              sh "python3 ./activate_version.py ${PREVIOUSVERSION} STAGING"
            }
          }
        }
      }
      // If STAGING has errors
      currentBuild.result = 'ABORTED'
      mail body: "Smoke tests failed in Staging. Failed build is here: ${env.BUILD_URL}" ,
            from: 'csc-jenkins@redhat.com',
            replyTo: 'rlong@redhat.com',
            subject: 'CSC build: STAGING smoke tests failed',
            to: 'rlong@redhat.com,khala@redhat.com'
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
          withEnv([
            "EDGERCPATH=$EDGERC"
          ]) {
            sh "python3 ./activate_version.py ${NEWVERSION} PRODUCTION $ENVSTR true"
          }
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
      if (RUN_SMOKE_TESTS) {
        openShiftUtils.withNode {
          withCredentials([
            string(credentialsId: "vaultRoleId", variable: 'DYNACONF_IQE_VAULT_ROLE_ID'),
            string(credentialsId: "vaultSecretId", variable: 'DYNACONF_IQE_VAULT_SECRET_ID'),
          ]) {
            // set some env variables for authentication in the iqe-core pod
            withEnv([
              "DYNACONF_IQE_VAULT_ROLE_ID=$DYNACONF_IQE_VAULT_ROLE_ID",
              "DYNACONF_IQE_VAULT_SECRET_ID=$DYNACONF_IQE_VAULT_SECRET_ID",
              "DYNACONF_IQE_VAULT_LOADER_ENABLED=true",
              "ENV_FOR_DYNACONF=prod"
            ]) {
              // install akamai and 3scale plugins, run smoke tests
              sh "iqe plugin install akamai 3scale"
              sh "IQE_AKAMAI_CERTIFI=true DYNACONF_AKAMAI=\'@json {\"release\":\"${RELEASESTR}\"}\' iqe tests plugin akamai -s -m ${PRODTESTSTR}"
              sh "iqe tests plugin akamai -k 'test_api.py' -m prod"
              sh "iqe tests plugin 3scale --akamai-production -m akamai_smoke"
            }
          }
        }
      }
      else {
        sh "echo Smoke tests cannot run against STAGE environment as it requires VPN connection"
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
            withEnv([
              "EDGERCPATH=$EDGERC"
            ]) {
              sh "python3 ./activate_version.py ${PREVIOUSVERSION} PRODUCTION"
            }
          }
        }
      }
      // If PRODUCTION has errors
      currentBuild.result = 'ABORTED'
      mail body: "Smoke tests failed in production. Failed build is here: ${env.BUILD_URL}" ,
            from: 'csc-jenkins@redhat.com',
            replyTo: 'rlong@redhat.com',
            subject: 'CSC build: PROD smoke tests failed',
            to: 'rlong@redhat.com,khala@redhat.com'
      error('Smoke tests failed in PRODUCTION. All changes have been rolled back.')
    }
  }
}
