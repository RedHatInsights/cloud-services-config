import yaml
import json
import re
import urllib3
import requests
import ConfigParser
import os
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

def getEdgeGridAuthFromFile(path="~/.edgerc"):
    config = ConfigParser.RawConfigParser()
    config.read(os.path.expanduser(path))
    return EdgeGridAuth(
        client_token=config.get("default", "client_token"),
        client_secret=config.get("default", "client_secret"),
        access_token=config.get("default", "access_token")
    )

def getLatestVersionNumber(env="PRODUCTION"):
    data = json.loads(akamaiGet("/papi/v1/properties/prp_516561/versions/latest?activatedOn={}&contractId=ctr_3-1MMN3Z&groupId=grp_134508".format(env)))
    return data["versions"]["items"][0]["propertyVersion"]
    
# TODO: Are we even going to use this one?
def getPropertyData():
    return json.loads(akamaiGet("/papi/v1/properties/prp_516561/versions/153/rules?contractId=ctr_3-1MMN3Z&groupId=grp_134508&validateRules=true&validateMode=fast"))

def createNewVersion():
    # Get the number of the latest prod version to use as a base
    latest_prod_version = getLatestVersionNumber("PRODUCTION")
    body = {}
    body["createFromVersion"] = latest_prod_version
    
    # Create temp response content so I can test without creating a million versions in Akamai
    # TODO: uncomment next line and delete the two following ones
    # response_content = json.loads(akamaiPost("/papi/v1/properties/prp_516561/versions?contractId=ctr_3-1MMN3Z&groupId=grp_134508", body))
    response_content = {}
    response_content["versionLink"] = "/papi/v0/properties/prp_516561/versions/171?contractId=ctr_3-1MMN3Z&groupId=grp_134508"

    new_version = 0
    m = re.search('versions\/(.+?)\?contractId', response_content["versionLink"])
    if m:
        new_version = m.group(1)

    print("New version number {}".format(new_version))

    return new_version

def createRulesForEnv(master_config, global_path_prefix=""):
    # Temporarily using a sample rule for testing
    rules = getJSONFromFile("./data/sample_rule.json")

    # TODO: Go through master_config and create rules one at a time

    return rules

def updatePropertyRulesUsingConfig(version_number, master_config):
    rules_tree = getJSONFromFile("./data/rules_base.json")

    print("Before:")
    print(json.dumps(rules_tree))

    # TODO: Find this value dynamically instead of hardcoding since this could change
    # Need to be able to get a node by whether it says "Stable" or "Beta"
    rules_tree["rules"]["children"][2]["children"][1]["children"] = createRulesForEnv(master_config, "")
    rules_tree["rules"]["children"][2]["children"][2]["children"] = createRulesForEnv(master_config, "/beta")

    print("After:")
    print(json.dumps(rules_tree))

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
baseurl = "https://akab-fivf4v4qvlicqynr-uv7txgqiof4thfet.luna.akamaiapis.net"
s.auth = getEdgeGridAuthFromFile()

cs_config = getYMLFromFile("../main.yml")
# print("CS config:")
# print(cs_config)

# Get the number of the latest version running in Production
# http --auth-type edgegrid -a default: ":/papi/v1/properties/prp_516561/versions/latest?activatedOn=PRODUCTION&contractId=ctr_3-1MMN3Z&groupId=grp_134508"

# Create a new version every time once we"re done testing
# For now we"ll just build on v171
new_version_number = createNewVersion()

# Update the rules JSON using the cs configuration as a reference
updatePropertyRulesUsingConfig(new_version_number, cs_config)

# Activate on STAGING???




# property_data = getPropertyData()
# print("Property data:")
# print(json.dumps(property_data))

