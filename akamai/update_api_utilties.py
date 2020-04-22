import configparser
import json
import os
import requests
import sys
import time
import yaml
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from urllib.parse import urljoin

# These are simply local file helpers.
def getYMLFromFile(path="../main.yml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def getJSONFromFile(path):
    with open(path, "r") as f:
        return json.load(f)

def getYMLFromUrl(url):
    return yaml.safe_load(s.get(url, verify=False).content.decode('utf-8'))

def getPropertyIDForEnv(env):
    if env == "stage":
        return "prp_614339"
    else:
        return "prp_516561"

# Makes an API call requesting the latest version data for the property.
def getLatestVersionNumber(crc_env, akamai_env):
    print("API - Getting version of latest activation in {}...".format(akamai_env))
    data = json.loads(akamaiGet("/papi/v1/properties/{}/versions/latest?activatedOn={}&contractId=ctr_3-1MMN3Z&groupId=grp_134508".format(getPropertyIDForEnv(crc_env), akamai_env)))
    return data["versions"]["items"][0]["propertyVersion"]

# Makes an API call to activate the specified version on the specified environment.
def activateVersion(version_number, env="STAGING", crc_env="stage"):
    # "notifyEmails" is unfortunately required for this API call.
    # TODO: Set this to the team email list once that exists
    body = {
        "note": "Auto-generated activation",
        "useFastFallback": "false",
        "notifyEmails": [
            "aprice@redhat.com"
        ]
    }
    body["propertyVersion"] = version_number
    body["network"] = env
    print("API - Activating version {} on {}...".format(version_number, env))
    response = json.loads(akamaiPost("/papi/v1/properties/{}/activations?contractId=ctr_3-1MMN3Z&groupId=grp_134508".format(getPropertyIDForEnv(crc_env)),body))
    err = False

    # If there are any warnings in the property, it'll return a status 400 with a list of warnings.
    # Acknowledging these warnings in the request body will allow the activation to work.
    if "activationLink" in response:
        print("Wow, first try! Version {} activated on {}.".format(version_number, env))
    elif "status" in response and response["status"] == 400 and "warnings" in response:
        warnings = []
        for w in response["warnings"]:
            warnings.append(w["messageId"])
        body["acknowledgeWarnings"] = warnings
        print("API - First activation request gave warnings. Acknowledging...")
        response = json.loads(akamaiPost("/papi/v1/properties/{}/activations?contractId=ctr_3-1MMN3Z&groupId=grp_134508".format(getPropertyIDForEnv(crc_env)),body))

        # If it fails again, give up.
        if "activationLink" in response:
            print("Version {} beginning activation on {}.".format(version_number, env))
        else:
            err = True
            print("Something went wrong while acknowledging warnings. Here's the response we got:")     
    else:
        err = True
        print("Something went wrong on the first activation attempt. Here's the response we got:")
    if err:
        print(json.dumps(response))
        print("The activaction failed. Please check out the above response to see what happened.") 

def waitForActiveVersion(version_number, env="STAGING", crc_env="stage"):
    print("Waiting for version {} to finish activating...".format(version_number))
    active_version = ""
    timeout = 180
    while active_version != version_number:
        time.sleep(10)
        try:
            active_version = getLatestVersionNumber(crc_env, env)
        except:
            print("Failed to retrieve current version")
        timeout -= 1
        if(timeout == 0):
            sys.exit("Retried too many times! New version not activated.")
        print("Property active in {} is v{}".format(env, active_version))
    print("Success! Property v{} now active on {}.".format(active_version, env))

# Makes an API call requesting the latest version data for the property.
def getLatestVersionNumber(env):
    print("API - Getting version of latest activation in {}...".format(env))
    data = json.loads(akamaiGet("/papi/v1/properties/prp_516561/versions/latest?activatedOn={}&contractId=ctr_3-1MMN3Z&groupId=grp_134508".format(env)))
    return data["versions"]["items"][0]["propertyVersion"]

# Makes an API call to activate the specified version on the specified environment.
def activateVersion(version_number, env="STAGING"):
    # "notifyEmails" is unfortunately required for this API call.
    # TODO: Set this to the team email list once that exists
    body = {
        "note": "Auto-generated activation",
        "useFastFallback": "false",
        "notifyEmails": [
            "aprice@redhat.com"
        ]
    }
    body["propertyVersion"] = version_number
    body["network"] = env
    print("API - Activating version {} on {}...".format(version_number, env))
    response = json.loads(akamaiPost("/papi/v1/properties/prp_516561/activations?contractId=ctr_3-1MMN3Z&groupId=grp_134508",body))
    err = False

    # If there are any warnings in the property, it'll return a status 400 with a list of warnings.
    # Acknowledging these warnings in the request body will allow the activation to work.
    if "activationLink" in response:
        print("Wow, first try! Version {} activated on {}.".format(version_number, env))
    elif "status" in response and response["status"] == 400 and "warnings" in response:
        warnings = []
        for w in response["warnings"]:
            warnings.append(w["messageId"])
        body["acknowledgeWarnings"] = warnings
        print("API - First activation request gave warnings. Acknowledging...")
        response = json.loads(akamaiPost("/papi/v1/properties/prp_516561/activations?contractId=ctr_3-1MMN3Z&groupId=grp_134508",body))

        # If it fails again, give up.
        if "activationLink" in response:
            print("Version {} beginning activation on {}.".format(version_number, env))
        else:
            err = True
            print("Something went wrong while acknowledging warnings. Here's the response we got:")     
    else:
        err = True
        print("Something went wrong on the first activation attempt. Here's the response we got:")
    if err:
        print(json.dumps(response))
        print("The activaction failed. Please check out the above response to see what happened.") 

# Initializes the EdgeGrid auth using the .edgerc file (or some passed-in config).
def initEdgeGridAuth(path="~/.edgerc"):
    # If the config file was passed in, use that.
    if len(sys.argv) > 1:
        path = sys.argv[1]
    config = configparser.RawConfigParser()
    config.read(os.path.expanduser(path))

    # TODO: We might actually be able to authenticate without EdgeGridAuth,
    # which would reduce the number of dependencies.
    s.auth = EdgeGridAuth(
        client_token=config.get("default", "client_token"),
        client_secret=config.get("default", "client_secret"),
        access_token=config.get("default", "access_token")
    )

# Gets the hostname from the .edgerc file (or some passed-in config).
def getHostFromConfig(path="~/.edgerc"):
    # If the config file was passed in, use that.
    if len(sys.argv) > 1:
        path = sys.argv[1]
    config = configparser.RawConfigParser()
    config.read(os.path.expanduser(path))
    return config.get("default", "host")

# HTTP Helper Functions 
def akamaiGet(url):
    return s.get(urljoin(base_url, url)).content

def akamaiPost(url, body):
    return s.post(urljoin(base_url, url), json=body).content

def akamaiPut(url, body):
    return s.put(urljoin(base_url, url), json=body).content

# Set up connectivity. Global var because it's a session that's used in multiple functions.
s = requests.Session()

# Get the base url using the provided config
base_url = "https://" + getHostFromConfig()
