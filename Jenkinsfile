@Library("github.com/RedHatInsights/insights-pipeline-lib@v3") _
import groovy.json.JsonSlurper

node {
  // Only run one build at a time; otherwise they'll fail since you can only have one Akamai activation at a time
  properties([disableConcurrentBuilds()])
  NAVLIST = "ansible application-services docs insights landing openshift rhel settings user-preferences"
  stage ("Create Backup old YAML/JSON files") {
    BRANCH = env.BRANCH_NAME.replaceAll("origin/", "")
    if (BRANCH == "prod-stable") {
      PREFIX = ""
      PRODTESTSTR = "\'prod and stable\'"
      RELEASESTR = "stable"
      ENVSTR = "prod"
    } else if (BRANCH == "prod-beta") {
      PREFIX = "beta/"
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
      CSC_CONFIG_PATH = "https://console.redhat.com/${PREFIX}config"
      RUN_SMOKE_TESTS = true
    } else {
      AKAMAI_APP_PATH = "/822386/${ENVSTR}/${PREFIX}config"
      CSC_CONFIG_PATH = "https://console.redhat.com/${ENVSTR}/${PREFIX}config"
      RUN_SMOKE_TESTS = false   // cannot run smoke tests on stage as it requires vpn
    }

    // on prod envs, create backups of config files
    if (RUN_SMOKE_TESTS) {
      sh "wget -O main.yml.bak ${CSC_CONFIG_PATH}/main.yml"
      sh "wget -O releases.yml.bak ${CSC_CONFIG_PATH}/releases.yml"
      // backup chrome nav files
      sh "mkdir -p ./chrome.bak"
      for (nav in NAVLIST.split(' ')) {
        sh "wget -O ./chrome.bak/${nav}-navigation.json ${CSC_CONFIG_PATH}/chrome/${nav}-navigation.json"
      }
      // also get fed-modules.json
      sh "wget -O ./chrome.bak/fed-modules.json ${CSC_CONFIG_PATH}/chrome/fed-modules.json"
    }
  }

  stage ("Sync on Akamai staging") {
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
          rsync -arv -e \"ssh -2\" ./chrome/*.json sshacs@cloud-unprotected.upload.akamai.com:${AKAMAI_APP_PATH}/chrome
        """
      }

      // set akamai fast purge env
      openShiftUtils.withJnlpNode(        
        image: "quay.io/redhatqe/origin-jenkins-agent-akamai:4.9",
        namespace: "insights-dev-jenkins"
      ) {
        sh "wget https://raw.githubusercontent.com/RedHatInsights/cloud-services-config/${ENVSTR}-${RELEASESTR}/akamai/cache_buster/bust_cache.py"
        // get akamai fast purge credentials
        withCredentials([file(credentialsId: "jenkins-eccu-cache-purge", variable: 'EDGERC')]) {
          sh "python3 bust_cache.py $EDGERC ${BRANCH} ${NAVLIST}"
        }
        // we have to wait 5-10s until akamai fast purge takes effect
        sleep(10)
      }
    }
  }

  stage ("Run Akamai Production Smoke Tests") {
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
      // Re-upload the old main.yml/json files
      configFileProvider([configFile(fileId: "9f0c91bc-4feb-4076-9f3e-13da94ff3cef", variable: "AKAMAI_HOST_KEY")]) {
        sh "rm main.yml"
        sh "cp main.yml.bak main.yml"
        sh "rm releases.yml"
        sh "cp releases.yml.bak releases.yml"
        sh "rm -r chrome"
        sh "cp -r chrome.bak chrome"
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
            rsync -arv -e \"ssh -2\" ./chrome/*.json sshacs@cloud-unprotected.upload.akamai.com:${AKAMAI_APP_PATH}/chrome
          """
        }
      }

      openShiftUtils.withJnlpNode(
        image: "quay.io/redhatqe/origin-jenkins-agent-akamai:4.9",
        namespace: "insights-dev-jenkins"
      ) {
        sh "wget https://raw.githubusercontent.com/RedHatInsights/cloud-services-config/${ENVSTR}-${RELEASESTR}/akamai/cache_buster/bust_cache.py"
        // get akamai fast purge credentials
        withCredentials([file(credentialsId: "jenkins-eccu-cache-purge", variable: 'EDGERC')]) {
          sh "python3 bust_cache.py $EDGERC ${BRANCH} ${NAVLIST}"
        }
        // we have to wait 5-10s until akamai fast purge takes effect
        sleep(10)
      }

      // If smoke tests have errors
      currentBuild.result = 'ABORTED'
      mail body: "CSC smoke tests failed. Failed build is here: ${env.BUILD_URL}" ,
            from: 'csc-jenkins@redhat.com',
            replyTo: 'rlong@redhat.com',
            subject: 'CSC build: Smoke tests failed',
            to: 'csc-pipeline-failures@redhat.com'
      error('Smoke tests failed! Changes have been rolled back.')
    }
  }
}
