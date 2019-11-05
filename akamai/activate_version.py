import json
import sys
import update_api_utilties as util

def main():
    # Authenticate with EdgeGrid
    # TODO: Change this authentication to get rid of the httpie dependency. Apprently there's a vulnerability
    util.initEdgeGridAuth()

    if len(sys.argv) > 2:
        version_to_activate = sys.argv[2]
    else:
        sys.exit("Activation failed: no property version number specified")
    if len(sys.argv) > 3:
        environment = sys.argv[3]
    else:
        environment = "STAGING"
    
    previous_version = util.getLatestVersionNumber(environment)
    with open("previousversion.txt", "w") as f:
        f.write(str(previous_version))

    print(">>>>>>>>>>>>>>>>>>>>>>>> Beginning activation in {}! <<<<<<<<<<<<<<<<<<<<<<<<".format(environment))
    print("Activating v{}".format(version_to_activate))

    # Activate on given env
    util.activateVersion(version_to_activate, environment)


if __name__== "__main__":
    main()
