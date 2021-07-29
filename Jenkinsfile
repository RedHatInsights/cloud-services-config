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
      CSC_CONFIG_PATH = "https://console.redhat.com/${PREFIX}config"
      RUN_SMOKE_TESTS = true
    } else {
      AKAMAI_APP_PATH = "/822386/${ENVSTR}/${PREFIX}config"
      CSC_CONFIG_PATH = "https://console.redhat.com/${ENVSTR}/${PREFIX}config"
      RUN_SMOKE_TESTS = false   // cannot run smoke tests on stage as it requires vpn
    }

    sh "wget -O main.yml.bak ${CSC_CONFIG_PATH}/main.yml"
    sh "wget -O releases.yml.bak ${CSC_CONFIG_PATH}/releases.yml"
    // we have to wait with the backup after first upload to akamai
    // sh "wget -r -np -A \"*.json\" -nd ${CSC_CONFIG_PATH}/chrome/ -P ./chrome.bak"
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
    }
  }
}