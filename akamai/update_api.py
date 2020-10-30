import copy
import json
import re
import sys
import update_api_utilties as util

# Creates a new version of the property in Akamai,
# which is based off of the latest active version in the given environment.
def createNewVersion(crc_env="stage", property_env="STAGING"):
    # Get the number of the latest prod version to use as a base
    previous_version = util.getLatestVersionNumber(crc_env, property_env)

    # Save this number for later: create a file that contains the latest version number
    with open("previousversion.txt", "w") as f:
        f.write(str(previous_version))

    body = {
        "createFromVersion": previous_version
    }
    
    print("API - Creating new version based on v{}".format(previous_version))
    response_content = json.loads(util.akamaiPost("/papi/v1/properties/{}/versions?contractId=ctr_3-1MMN3Z&groupId=grp_134508".format(util.getPropertyIDForEnv(crc_env)),body))

    new_version = 0
    m = re.search('versions\/(.+?)\?contractId', response_content["versionLink"])
    if m:
        new_version = m.group(1)
    print("Version {} created.".format(new_version))

    # Save this number for later: create a file that contains the new version number
    with open("newversion.txt", "w") as f:
        f.write(str(new_version))
    return new_version

# Creates a list of rules in the correct Akamai PM structure based on
# the master_config (source of truth), and prepends paths with
# url_path_prefix as appropriate.
def createRulesForEnv(master_config, url_path_prefix="", content_path_prefix="", crc_env = "stage"):
    # First, add the rules for the landing page.

    if crc_env == "stage":
        rules = util.getJSONFromFileWithReplacements("./data/landing_page_rules.json", [("\"cloud.redhat.com\"", "\"cloud.stage.redhat.com\"")])
        rules.extend(util.getJSONFromFileWithReplacements("./data/storybook_rules.json", [("\"cloud.redhat.com\"", "\"cloud.stage.redhat.com\"")]))
    else:
        rules = util.getJSONFromFile("./data/landing_page_rules.json")
        rules.extend(util.getJSONFromFile("./data/storybook_rules.json"))

    # If either url path prefix or content path prefix exists, modify paths on landing page & storybook rules.
    for rule in rules:
        if rule["behaviors"][0]["name"] == "rewriteUrl" and rule["behaviors"][0]["options"]["behavior"] == "PREPEND" and "pentest" not in content_path_prefix:
            rules.remove(rule)
        if content_path_prefix != "":
            if rule["behaviors"][0]["name"] == "failAction":
                rule["behaviors"][0]["options"]["contentPath"] = content_path_prefix + rule["behaviors"][0]["options"]["contentPath"]
        if url_path_prefix != "":
            for x in range(len(rule["criteria"])):
                if rule["criteria"][x]["name"] == "path":
                    for y in range(len(rule["criteria"][x]["options"]["values"])):
                        if rule["criteria"][x]["options"]["values"][y] == "/":
                            rule["criteria"][x]["options"]["values"].append(url_path_prefix)
                        rule["criteria"][x]["options"]["values"][y] = url_path_prefix + rule["criteria"][x]["options"]["values"][y]

    # Create a template object to copy from (reduces number of read/write ops)
    if crc_env == "stage":
        rule_template = util.getJSONFromFileWithReplacements("./data/single_rule_template.json", [("\"cloud.redhat.com\"", "\"cloud.stage.redhat.com\"")])
    else:
        rule_template = util.getJSONFromFile("./data/single_rule_template.json")
    nomatch_template = util.getJSONFromFile("./data/no_match_criteria.json")

    # Creates rules for all the apps that follow a pattern.
    for key, app in master_config.items():
        if "frontend" in app and "paths" in app["frontend"] and not ("disabled_on_prod" in app and app["disabled_on_prod"]):
            app_rule = copy.deepcopy(rule_template)
            app_rule["name"] = "/" + key
            app_path = app["frontend"]["app_base"] if "app_base" in app["frontend"] else key
            app_rule["behaviors"][0]["options"]["contentPath"] = "{}/apps/{}/index.html".format(content_path_prefix, app_path)
            for frontend_path in app["frontend"]["paths"]:
                values = [url_path_prefix + frontend_path]
                values += [url_path_prefix + frontend_path + "/*"]
                app_rule["criteria"][0]["options"]["values"].extend(values)

            if "frontend_exclude" in app and len(app["frontend_exclude"]) > 0:
                app_criteria = copy.deepcopy(nomatch_template)
                for nomatch in app["frontend_exclude"]:
                    app_criteria["options"]["values"].append(url_path_prefix + nomatch)
                    app_criteria["options"]["values"].append(url_path_prefix + nomatch + "/*")
                app_rule["criteria"].append(app_criteria)

            rules.append(app_rule)

    return rules

# Makes an API call which updates the property version with a new rule tree.
def updatePropertyRulesUsingConfig(version_number, master_config_list, crc_env = "stage"):
    print("Creating new ruleset based on list of master configs...")
    frontend_rule_index = 5 if ("stage"==crc_env) else 4
    replacements = [
        ("<<prod-gateway-secret>>", util.getEnvVar("GATEWAYSECRET")),
        ("<<pentest-gateway-secret>>", util.getEnvVar("PENTESTGATEWAYSECRET")),
        ("<<certauth-gateway-secret>>", util.getEnvVar("CERTAUTHSECRET")),
        ("<<rhorchata-origin-json>>", util.readFileAsString(util.getEnvVar("RHORCHATAORIGINJSON"))),
        ("<<gateway-origin-json>>", util.readFileAsString(util.getEnvVar("GATEWAYORIGINJSON"))),
        ("<<turnpike-origin-json>>", util.readFileAsString(util.getEnvVar("TURNPIKEORIGINJSON"))),
        ("<<pentest-gateway-origin-json>>", util.readFileAsString(util.getEnvVar("PENTESTGATEWAYORIGINJSON"))),
        ("<<openshift-origin-json>>", util.readFileAsString(util.getEnvVar("OPENSHIFTORIGINJSON"))),
        ("<<openshift-origin-mirror-json>>", util.readFileAsString(util.getEnvVar("OPENSHIFTORIGINMIRRORJSON")))
    ]

    rules_tree = util.getJSONFromFileWithReplacements("./data/{}/base_rules.json".format(crc_env), replacements)

    parent_rule_template = util.getJSONFromFile("./data/base_env_rule.json")

    # Iterate through the configurations for each release
    for env in master_config_list:
        parent_rule = copy.deepcopy(parent_rule_template)
        parent_rule["name"] = "{} (AUTO-GENERATED)".format(env["name"])
        if ("url_prefix" not in env or env["url_prefix"] == ""):
            parent_rule["criteria"][0]["options"]["matchOperator"] = "DOES_NOT_MATCH_ONE_OF"
            parent_rule["criteria"][0]["options"]["values"].extend(["/api", "/api/*", "/mirror/openshift*", "/wss/*"])
            # Each env should exclude matches for other envs.
            for nomatch in (x for x in master_config_list if (x != env["name"] and "url_prefix" in x and x["url_prefix"] != "")):
                parent_rule["criteria"][0]["options"]["values"].extend([nomatch["url_prefix"], nomatch["url_prefix"] + "/*"])
        else:
            parent_rule["criteria"][0]["options"]["matchOperator"] = "MATCHES_ONE_OF"
            parent_rule["criteria"][0]["options"]["values"].extend([env["url_prefix"], env["url_prefix"] + "/*"])
        
        # Update pen-test cookie check, if necessary
        if ("cookie_required" in env and env["cookie_required"]):
            parent_rule["criteria"][1]["options"]["matchOperator"] = "EXISTS"
            
        parent_rule["children"] = createRulesForEnv(env["config"], env["url_prefix"], env["content_path_prefix"], crc_env)
        rules_tree["rules"]["children"][frontend_rule_index]["children"].append(parent_rule)

    # Update property with this new ruleset
    print("API - Updating rule tree...")
    response = json.loads(util.akamaiPut("/papi/v1/properties/{}/versions/{}/rules?contractId=ctr_3-1MMN3Z&groupId=grp_134508&validateRules=true&validateMode=full".format(util.getPropertyIDForEnv(crc_env), version_number),rules_tree))
    print("Response:")
    print(json.dumps(response))

def generateExclusions(frontend_path, config):
    exclusions = []
    for key in (x for x in config.keys() if "frontend" in config[x] and "paths" in config[x]["frontend"] and frontend_path not in config[x]["frontend"]["paths"]):
        for path in config[key]["frontend"]["paths"]:
            if frontend_path in path:
                exclusions.append(path)
    return exclusions

def generateConfigForBranch(source_branch, url_prefix, local_branch):
    # Get main.yml from c.rh.c Prod if we can
    if source_branch == local_branch:
        config = util.getYMLFromFile("../main.yml")
    elif source_branch.startswith("prod"):
        config = util.getYMLFromUrl("https://cloud.redhat.com{}/config/main.yml".format(url_prefix))
    else:
        # Otherwise, get it from github; Jenkins can't talk to our pre-prod envs.
        config = util.getYMLFromUrl("https://raw.githubusercontent.com/RedHatInsights/cloud-services-config/{}/main.yml".format(source_branch))

    # For every app in config, check all other apps to see if they have a frontend_path that contains its frontend_paths.
    for key in (x for x in config.keys() if "frontend" in config[x] and "paths" in config[x]["frontend"]):
        exclusions = []
        for fe_path in config[key]["frontend"]["paths"]:
            exclusions.extend(generateExclusions(fe_path, config))
        config[key]["frontend_exclude"] = exclusions
    return config
    
def main():
    # Get the Cloud Services config files (main source of truth) for all configured releases
    releases = util.getYMLFromFile("../releases.yml")

    # This arg will be either "prod-stable" or "prod-beta", and tells us which release our local main.yml is for.
    # This guarantees that the newest main.yml is used instead of the one it intends to replace.
    if len(sys.argv) > 3:
        local_branch = sys.argv[3]
    else:
        local_branch = "prod-stable"

    if len(sys.argv) > 2:
        crc_env = sys.argv[2]
    else:
        crc_env = "stage"

    crc_env_prefix = ""
    if crc_env == "stage":
        crc_env_prefix = "/stage"

    cs_config_list = []
    for env in releases:
        source_branch = releases[env]["branch"].replace("prod", crc_env) if "branch" in releases[env] else ""
        url_prefix = releases[env]["url_prefix"] if "url_prefix" in releases[env] else ""
        content_path_prefix = crc_env_prefix + releases[env]["content_path_prefix"] if "content_path_prefix" in releases[env] else crc_env_prefix

        cs_config_list.append({
            "name": env,
            "url_prefix": url_prefix,
            "content_path_prefix": content_path_prefix,
            "cookie_required": releases[env]["cookie_required"] if "cookie_required" in releases[env] else False,
            "config": generateConfigForBranch(source_branch, url_prefix, local_branch)
        })

    if len(sys.argv) > 1:
        property_env = sys.argv[1]
    else:
        property_env = "STAGING"

    # Authenticate with EdgeGrid
    util.initEdgeGridAuth()

    # Create a new version based off of the active Prod version
    new_version_number = createNewVersion(crc_env, property_env)

    # Update the rules JSON using the CS configuration as a reference
    updatePropertyRulesUsingConfig(new_version_number, cs_config_list, crc_env)

    # Activate version
    util.activateVersion(new_version_number, property_env, crc_env)

    # Wait for new version to be active
    util.waitForActiveVersion(int(new_version_number), property_env, crc_env)

if __name__== "__main__":
    main()
