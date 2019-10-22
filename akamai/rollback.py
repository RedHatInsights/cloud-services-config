import json
import sys
import update_api_utilties as util

def main():
    # Authenticate with EdgeGrid
    # TODO: Change this authentication to get rid of the httpie dependency. Apprently there's a vulnerability
    util.initEdgeGridAuth()

    print(">>>>>>>>>>>>>>>>>>>>>>>> Beginning rollback to previous version! <<<<<<<<<<<<<<<<<<<<<<<<")
    if len(sys.argv) > 2:
        rollback_version = sys.argv[2]
    else:
        rollback_version = -1
    print("Rolling back to v{}".format(rollback_version))

    # Activate on STAGING
    util.activateVersion(rollback_version, "STAGING")


if __name__== "__main__":
    main()