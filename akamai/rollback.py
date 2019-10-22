import json
import sys
import update_api_utilties as util

def main():
    # Authenticate with EdgeGrid
    # TODO: Change this authentication to get rid of the httpie dependency. Apprently there's a vulnerability
    util.initEdgeGridAuth()

    if len(sys.argv) > 2:
        rollback_version = sys.argv[2]
    else:
        sys.exit("Rollback failed: no rollback version number specified")
    if len(sys.argv) > 3:
        environment = sys.argv[3]
    else:
        environment = "STAGING"
    
    print(">>>>>>>>>>>>>>>>>>>>>>>> Beginning rollback to previous version in {}! <<<<<<<<<<<<<<<<<<<<<<<<".format(environment))
    print("Rolling back to v{}".format(rollback_version))

    # Activate on STAGING
    util.activateVersion(rollback_version, "STAGING")


if __name__== "__main__":
    main()
