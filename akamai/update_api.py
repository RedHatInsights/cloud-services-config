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

# Set up Edgegrid auth
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
    return "https://" + config.get("default", "host")

def getLatestVersionNumber(env="PRODUCTION"):
    data = json.loads(akamaiGet("/papi/v1/properties/prp_516561/versions/latest?activatedOn={}&contractId=ctr_3-1MMN3Z&groupId=grp_134508".format(env)))
    return data["versions"]["items"][0]["propertyVersion"]
    
def createNewVersion():
    # Get the number of the latest prod version to use as a base
    latest_prod_version = getLatestVersionNumber("PRODUCTION")
    body = {}
    body["createFromVersion"] = latest_prod_version
    
    # Create temp response content so I can test without creating a million versions in Akamai
    # TODO: uncomment next line and delete the two following ones
    # response_content = json.loads(akamaiPost("/papi/v1/properties/prp_516561/versions?contractId=ctr_3-1MMN3Z&groupId=grp_134508", body))
    response_content = {}
    response_content["versionLink"] = "/papi/v0/properties/prp_516561/versions/172?contractId=ctr_3-1MMN3Z&groupId=grp_134508"

    new_version = 0
    m = re.search('versions\/(.+?)\?contractId', response_content["versionLink"])
    if m:
        new_version = m.group(1)

    print("New version number {}".format(new_version))

    return new_version

def createRulesForEnv(master_config, global_path_prefix=""):
    # First, add the rules for the landing page.
    rules = getJSONFromFile("./data/landing_page_rules.json")

    # If global path prefix exists, modify paths on landing page rules.
    # TODO: Loop instead
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
                app_rule["criteria"][0]["options"]["values"] += [global_path_prefix + frontend_path, global_path_prefix + frontend_path + "/*"]

            if "frontend_exclude" in master_config[app]:
                app_criteria = copy.deepcopy(nomatch_template)
                for nomatch in master_config[app]["frontend_exclude"]:
                    app_criteria["options"]["values"].append(global_path_prefix + nomatch)
                    app_criteria["options"]["values"].append(global_path_prefix + nomatch + "/*")
                app_rule["criteria"].append(app_criteria)

            rules.append(app_rule)

    return rules

def updatePropertyRulesUsingConfig(version_number, master_config):
    rules_tree = getJSONFromFile("./data/base_rules.json")

    # TODO: Find this value dynamically instead of hardcoding since this could change
    # Need to be able to get a node by whether it says "Stable" or "Beta"
    rules_tree["rules"]["children"][2]["children"][1]["children"] = createRulesForEnv(master_config, "")
    rules_tree["rules"]["children"][2]["children"][2]["children"] = createRulesForEnv(master_config, "/beta")

    # Update property with this new ruleset
    response = json.loads(akamaiPut("/papi/v1/properties/prp_516561/versions/{}/rules?contractId=ctr_3-1MMN3Z&groupId=grp_134508&validateRules=true&validateMode=full".format(version_number), rules_tree))
    print("update response:")
    print(json.dumps(response))

def akamaiGet(url):
    return s.get(urljoin(baseurl, url)).content

def akamaiPost(url, body):
    return s.post(urljoin(baseurl, url), json=body).content

def akamaiPut(url, body):
    return s.put(urljoin(baseurl, url), json=body).content


print("Script started")

s.auth = getEdgeGridAuthFromConfig()
baseurl = getHostFromConfig()

cs_config = getYMLFromFile("../main.yml")

# Get the number of the latest version running in Production
# http --auth-type edgegrid -a default: ":/papi/v1/properties/prp_516561/versions/latest?activatedOn=PRODUCTION&contractId=ctr_3-1MMN3Z&groupId=grp_134508"

# Create a new version every time once we"re done testing
new_version_number = createNewVersion()

# Update the rules JSON using the cs configuration as a reference
updatePropertyRulesUsingConfig(new_version_number, cs_config)

# Activate on STAGING???

