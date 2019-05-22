import copy
import json
import re
import requests
import update_api_utilties as util

#global variables
# Set up connectivity
s = requests.Session()
# Get the base url using the 
baseurl = "https://" + util.getHostFromConfig()

def getLatestVersionNumber(env="PRODUCTION"):
    print("API - Getting version of latest activation in {}...".format(env))
    data = json.loads(util.akamaiGet("/papi/v1/properties/prp_516561/versions/latest?activatedOn={}&contractId=ctr_3-1MMN3Z&groupId=grp_134508".format(env),baseurl, s))
    return data["versions"]["items"][0]["propertyVersion"]

def createNewVersion():
    # Get the number of the latest prod version to use as a base
    latest_prod_version = getLatestVersionNumber("PRODUCTION")
    body = {}
    body["createFromVersion"] = latest_prod_version
    
    # Create temp response content so I can test without creating a million versions in Akamai
    print("API - Creating new version based on v{}".format(latest_prod_version))
    response_content = json.loads(util.akamaiPost("/papi/v1/properties/prp_516561/versions?contractId=ctr_3-1MMN3Z&groupId=grp_134508",baseurl, body, s))

    new_version = 0
    m = re.search('versions\/(.+?)\?contractId', response_content["versionLink"])
    if m:
        new_version = m.group(1)
    print("Version {} created.".format(new_version))
    return new_version

def createRulesForEnv(master_config, global_path_prefix=""):
    # First, add the rules for the landing page.
    rules = util.getJSONFromFile("./data/landing_page_rules.json")
    rules.extend(util.getJSONFromFile("./data/storybook_rules.json"))

    # If global path prefix exists, modify paths on landing page rules.
    if global_path_prefix != "":
        for rule in rules:
            if rule["behaviors"][0]["name"] == "failAction":
                rule["behaviors"][0]["options"]["contentPath"] = global_path_prefix + rule["behaviors"][0]["options"]["contentPath"]
            if rule["criteria"][0]["name"] == "path":
                rule["criteria"][0]["options"]["values"][0] = global_path_prefix + rule["criteria"][0]["options"]["values"][0]

    # Create a template object to copy from
    rule_template = util.getJSONFromFile("./data/single_rule_template.json")
    nomatch_template = util.getJSONFromFile("./data/no_match_criteria.json")

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
    rules_tree = util.getJSONFromFile("./data/base_rules.json")

    # TODO: Find this value dynamically instead of hardcoding since this could change
    # Need to be able to get a node by whether it says "Stable" or "Beta"
    rules_tree["rules"]["children"][2]["children"][1]["children"] = createRulesForEnv(master_config, "")
    rules_tree["rules"]["children"][2]["children"][2]["children"] = createRulesForEnv(master_config, "/beta")

    # Update property with this new ruleset
    print("API - Updating rule tree...")
    response = json.loads(util.akamaiPut("/papi/v1/properties/prp_516561/versions/{}/rules?contractId=ctr_3-1MMN3Z&groupId=grp_134508&validateRules=true&validateMode=full".format(version_number),baseurl, rules_tree, s))

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
    response = json.loads(util.akamaiPost("/papi/v1/properties/prp_516561/activations?contractId=ctr_3-1MMN3Z&groupId=grp_134508",baseurl, body, s))

    # If there are any warnings in the property, it'll return a status 400 with a list of warnings.
    # Acknowledging these warnings in the request body will allow the activation to work.
    if "status" in response and response["status"] == 400:
        warnings = []
        for w in response["warnings"]:
            warnings.append(w["messageId"])
        body["acknowledgeWarnings"] = warnings
        print("API - First activation request gave warnings. Acknowledging...")
        response = json.loads(util.akamaiPost("/papi/v1/properties/prp_516561/activations?contractId=ctr_3-1MMN3Z&groupId=grp_134508",baseurl, body, s))

        # If it fails again, give up.
        if "status" in response:
            print("Something went wrong; here's the response we got:")
            print(json.dumps(response))
            print("The activaction failed. Please check out the above response and see what happened.")
        else:
            print("Success! Version {} activated on {}.".format(version_number, env))



def main():    

    # Authenticate session with user's local EdgeGrid config file (~/.edgerc)
    s.auth = util.getEdgeGridAuthFromConfig()

    # Get the Cloud Services config file (main source of truth)
    cs_config = util.getYMLFromFile("../main.yml")

    # Create a new version based off of the active Prod version
    new_version_number = createNewVersion()

    # Update the rules JSON using the CS configuration as a reference
    updatePropertyRulesUsingConfig(new_version_number, cs_config)

    # Activate on STAGING
    activateVersion(new_version_number, "STAGING")

if __name__== "__main__":
    main()
