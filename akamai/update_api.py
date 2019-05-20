import yaml
import json
import re
import urllib3
import requests
import ConfigParser
import os
import copy
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from urlparse import urljoin

# Set up connectivity
http = urllib3.PoolManager()
s = requests.Session()

# Utility functions
def getYMLFromFile(path="../main.yml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def getJSONFromFile(path):
    with open(path, "r") as f:
        return json.load(f)

def getEdgeGridAuthFromConfig(path="~/.edgerc"):
    config = ConfigParser.RawConfigParser()
    config.read(os.path.expanduser(path))
    return EdgeGridAuth(
        client_token=config.get("default", "client_token"),
        client_secret=config.get("default", "client_secret"),
        access_token=config.get("default", "access_token")
    )

def getHostFromConfig(path="~/.edgerc"):
    config = ConfigParser.RawConfigParser()
    config.read(os.path.expanduser(path))
    return config.get("default", "host")

def getLatestVersionNumber(env="PRODUCTION"):
    print("API - Getting version of latest activation in {}...".format(env))
    data = json.loads(akamaiGet("/papi/v1/properties/prp_516561/versions/latest?activatedOn={}&contractId=ctr_3-1MMN3Z&groupId=grp_134508".format(env)))
    return data["versions"]["items"][0]["propertyVersion"]
    
def createNewVersion():
    # Get the number of the latest prod version to use as a base
    latest_prod_version = getLatestVersionNumber("PRODUCTION")
    body = {}
    body["createFromVersion"] = latest_prod_version
    
    # Create temp response content so I can test without creating a million versions in Akamai
    print("API - Creating new version based on v{}".format(latest_prod_version))
    response_content = json.loads(akamaiPost("/papi/v1/properties/prp_516561/versions?contractId=ctr_3-1MMN3Z&groupId=grp_134508", body))

    new_version = 0
    m = re.search('versions\/(.+?)\?contractId', response_content["versionLink"])
    if m:
        new_version = m.group(1)
    print("Version {} created.".format(new_version))
    return new_version

def createRulesForEnv(master_config, global_path_prefix=""):
    # First, add the rules for the landing page.
    rules = getJSONFromFile("./data/landing_page_rules.json")
    rules.extend(getJSONFromFile("./data/storybook_rules.json"))

    # If global path prefix exists, modify paths on landing page rules.
    if global_path_prefix != "":
        for rule in rules:
            if rule["behaviors"][0]["name"] == "failAction":
                rule["behaviors"][0]["options"]["contentPath"] = global_path_prefix + rule["behaviors"][0]["options"]["contentPath"]
            if rule["criteria"][0]["name"] == "path":
                rule["criteria"][0]["options"]["values"][0] = global_path_prefix + rule["criteria"][0]["options"]["values"][0]

    # Create a template object to copy from
    rule_template = getJSONFromFile("./data/single_rule_template.json")
    nomatch_template = getJSONFromFile("./data/no_match_criteria.json")

    # Group Config section
    for app in master_config:
        if "frontend_paths" in master_config[app]:
            app_rule = copy.deepcopy(rule_template)
            app_rule["name"] = "/" + app
            app_rule["behaviors"][0]["options"]["contentPath"] = "{}/apps/{}/index.html".format(global_path_prefix, app)
            for frontend_path in master_config[app]["frontend_paths"]:
                values = [global_path_prefix + frontend_path]
                if "capture_path_additions" in master_config[app] and master_config[app]["capture_path_additions"]:
                    values += [global_path_prefix + frontend_path + "/*"]
                else:
                    values += [global_path_prefix + frontend_path + "/"]
                app_rule["criteria"][0]["options"]["values"].extend(values)

                if "frontend_exclude" in master_config[app]:
                    app_criteria = copy.deepcopy(nomatch_template)
                    for nomatch in master_config[app]["frontend_exclude"]:
                        app_criteria["options"]["values"].append(global_path_prefix + nomatch)
                        app_criteria["options"]["values"].append(global_path_prefix + nomatch + "/*")
                    app_rule["criteria"].append(app_criteria)

            rules.append(app_rule)

    return rules

def updatePropertyRulesUsingConfig(version_number, master_config):
    print("Creating new ruleset based on master config...")
    rules_tree = getJSONFromFile("./data/base_rules.json")

    # TODO: Find this value dynamically instead of hardcoding since this could change
    # Need to be able to get a node by whether it says "Stable" or "Beta"
    rules_tree["rules"]["children"][2]["children"][1]["children"] = createRulesForEnv(master_config, "")
    rules_tree["rules"]["children"][2]["children"][2]["children"] = createRulesForEnv(master_config, "/beta")

    # Update property with this new ruleset
    print("API - Updating rule tree...")
    response = json.loads(akamaiPut("/papi/v1/properties/prp_516561/versions/{}/rules?contractId=ctr_3-1MMN3Z&groupId=grp_134508&validateRules=true&validateMode=full".format(version_number), rules_tree))

def activateVersion(version_number, env="STAGING"):
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
    response = json.loads(akamaiPost("/papi/v1/properties/prp_516561/activations?contractId=ctr_3-1MMN3Z&groupId=grp_134508", body))

    # If there are any warnings in the property, it'll return a status 400 with a list of warnings.
    # Acknowledging these warnings in the request body will allow the activation to work.
    if "status" in response and response["status"] == 400:
        warnings = []
        for w in response["warnings"]:
            warnings.append(w["messageId"])
        body["acknowledgeWarnings"] = warnings
        print("API - First activation request gave warnings. Acknowledging...")
        response = json.loads(akamaiPost("/papi/v1/properties/prp_516561/activations?contractId=ctr_3-1MMN3Z&groupId=grp_134508", body))

        # If it fails again, give up.
        if "status" in response:
            print("Something went wrong; here's the response we got:")
            print(json.dumps(response))
            print("The activaction failed. Please check out the above response and see what happened.")
        else:
            print("Success! Version {} activated on {}.".format(version_number, env))


def akamaiGet(url):
    return s.get(urljoin(baseurl, url)).content

def akamaiPost(url, body):
    return s.post(urljoin(baseurl, url), json=body).content

def akamaiPut(url, body):
    return s.put(urljoin(baseurl, url), json=body).content


# Authenticate session with user's local EdgeGrid config file (~/.edgerc)
s.auth = getEdgeGridAuthFromConfig()

# Get the base url using the 
baseurl = "https://" + getHostFromConfig()

# Get the Cloud Services config file (main source of truth)
cs_config = getYMLFromFile("../main.yml")

# Create a new version based off of the active Prod version
new_version_number = createNewVersion()

# Update the rules JSON using the CS configuration as a reference
updatePropertyRulesUsingConfig(new_version_number, cs_config)

# Activate on STAGING
activateVersion(new_version_number, "STAGING")
