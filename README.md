# About

This repo deals with the high-level configuration of Cloud Services. `main.yml` contains the source of truth for CS apps, and the `akamai` folder deals with updating our Akamai configuration.

# Akamai API Access

Before you can run the property-updating script locally, you need to have access to the Akamai API.
To do this, follow the steps located [here](https://developer.akamai.com/api/getting-started). In step 5 of this doc the guide instructs you to set the Access Level of the Diagnostics Tools API to READ_WRITE; do this but also set the Access Level of the Property Manager API (PAPI) to READ-Write. Otherwise you will not have authorization to the configurations of Cloud Services. Make sure that the `.edgerc` file you create is located in your `home` directory and has the credentials defined in the `[default]` section of the file.
If you're able to run the sample call at the end of the doc, you should be able to run the script. If you run into issues, there may be something wrong with your `.edgerc` file.

For more information on the Akamai API, read the [property manager docs](https://developer.akamai.com/api/core_features/property_manager/v1.html).
