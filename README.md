# About

This repo deals with the high-level configuration of Cloud Services. `main.yml` contains the source of truth for CS apps, and the `akamai` folder deals with updating our Akamai configuration.

# Adding Config for New Apps

To enable a new app in our environments, you need to create configuration for it in `main.yml`, and then create a PR to merge it in. 
Here is some example configuration that demonstrates the structure, using all required and optional properties:
```
{app_id}: 
    title: App Title
    api:
        versions:
            - v1
            - v2
    channel: '#some-slack-channel'
    description: App Title is a cool app that does business things for its users.
    deployment_repo: https://github.com/app-deployment-repo-url
    disabled_on_stable: true
    docs: https://link.to.docs.com/docs
    frontend:
        title: App Title Override
        paths:
            - /example/path
            - /another/example/path
        reload: reload/path
        sub_apps:
            -   id: app_id_1
                title: Some Sub App
                default: true
            -   id: app_id_2
                title: Another Sub App
        suppress_id: true
    git_repo: https://github.com/app-development-repo-url
    mailing_list: app-title@redhat.com
    top_level: false
```

## Required Properties (All Apps)
Each of the following properties is required for all apps:

### app_id
This is your app's ID. It's used as the path to your app, and must be unique.

### app_id.title
The main title for your app. This is what you want everyone to see when they use your app.

### app_id.deployment_repo
This is the location of your app's deployment repo (not development repo). These repos generally have `build` or `deploy` as a suffix.

## API Properties
The following properties are used if your app has an API:

### app_id.api.versions
This is the list of API versions your app can use. Since `v1` is the default, you'll usually want at least that one defined.

## Frontend Properties
The following properties are used if your app has a frontend:

### app_id.frontend.title
If you want the name of your app to appear differently on the frontend, set this property to override it.

### app_id.frontend.paths
This is the list of paths where your app will be located. These paths are appended to the end of the paths of its parent apps (if any).
For example, let's say your app `ex_app_id` is a sub-app of `parent_app`, which has a frontend path of `/parent-app`. If you add a frontend path of `/ex-app`, your app will be available at `/parent-app/ex-app`.

### app_id.frontend.sub_apps
If your app is a parent to any other apps, those apps should be listed here. 
Also, if your app has a parent app, or is listed under one of the top-level bundles (i.e. Insights, RHEL, Hybrid, etc), you should add your app to the appropriate sub_apps list.

### app_id.frontend.reload
This property is almost never needed, and will likely be deprecated. This property is commonly used for Settings apps, and tells Chrome where to navigate on reload.

### app_id.frontend.suppress_id
This property is almost never needed, and will likely be deprecated. This property is used if the app isn't a real app on disk, and only exists for navigation purposes. 
This removes the app ID on the frontend so that the nav bar works as expected.

## Other Optional Properties
The following properties aren't required for all apps, but may still apply to your app:

### app_id.channel
This is the ID of the slack channel on ansible.slack.com that you want automatic notifications to be posted to.

### app_id.description
This is a description of your app's purpose or functionalities, which is used by some other apps.

### app_id.disabled_on_stable
If set to `true`, this app will only exist in `beta`.

### app_id.docs
This is the link to your app's documentation.

### app_id.git_repo
This is the URL of the development (not deployment) repo for your app, i.e. the one you commit to.

### app_id.mailing_list
This is the mailing list associated with your project. Used to automate email notifications.

### app_id.top_level
If this is set to `true`, your app will be a top-level app, which is usually reserved for bundles (Insights, RHEL, Hybrid, Openshift, etc).
Use this if your app does not have a parent app or bundle.


# Akamai API Access

Before you can run the property-updating script locally, you need to have access to the Akamai API.
To do this, follow the steps located [here](https://developer.akamai.com/api/getting-started). In step 5 of this doc the guide instructs you to set the Access Level of the Diagnostics Tools API to READ_WRITE; do this but also set the Access Level of the Property Manager API (PAPI) to READ-Write. Otherwise you will not have authorization to the configurations of Cloud Services. Make sure that the `.edgerc` file you create is located in your `home` directory and has the credentials defined in the `[default]` section of the file.
If you're able to run the sample call at the end of the doc, you should be able to run the script. If you run into issues, there may be something wrong with your `.edgerc` file.

For more information on the Akamai API, read the [property manager docs](https://developer.akamai.com/api/core_features/property_manager/v1.html).

# Build Process

This repository has a webhook that automatically builds a [Jenkins job](https://jenkins-jenkins.5a9f.insights-dev.openshiftapps.com/job/akamai-config-deployer/) on every push. To configure this webhook, check the project's [webhook settings](https://github.com/RedHatInsights/cloud-services-config/settings/hooks)