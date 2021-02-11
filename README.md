# About

This repo deals with the high-level configuration of Cloud Services. `main.yml` contains the source of truth for CS apps, and the `akamai` folder deals with updating our Akamai configuration.

## Adding Config for New Apps

To enable a new app in our environments, you need to create configuration for it in `main.yml`, and then create a PR to merge it into the `ci-beta` branch. The configuration for the non-prod beta branches is kept in sync, so changes to `ci-beta` will automatically be merged into `nightly-beta` and `qa-beta`. When you need this config added to another environment (`prod-beta`, `ci-stable`, `qa-stable`, `prod-stable`), please open another PR for that environment. If you have any concerns about this process, feel free to ping #forum-cloudservices-sre on Slack for assistance.

Here is some example configuration that demonstrates the structure, using all required and optional properties:

```yml
{app_id}:
    title: App Title
    api:
        versions:
            - v1
            - v2
        subItems:
            oneApi:
                title: Some title
                versions:
                    - v1
    channel: '#some-slack-channel'
    description: App Title is a cool app that does business things for its users.
    deployment_repo: https://github.com/app-deployment-repo-url
    disabled_on_prod: true
    docs: https://link.to.docs.com/docs
    permissions:
        method: isOrgAdmin
        apps:
            - app_id_1
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
                permissions:
                    method: isEntitled
                    args:
                        - insights
            -   id: app_id_2
                title: Another Sub App
        suppress_id: true
    source_repo: https://github.com/app-development-repo-url
    mailing_list: app-title@redhat.com
    top_level: false
```

### Required Properties (All Apps)

Each of the following properties is required for all apps:

#### app_id

This is your app's ID. It's used as the path to your app, and must be unique.

#### app_id.title

The main title for your app. This is what you want everyone to see when they use your app.

#### app_id.deployment_repo

This is the location of your app's deployment repo (not development repo). These repos generally have `build` or `deploy` as a suffix.

### API Properties

The following properties are used if your app has an API:

#### app_id.api.versions

This is the list of API versions your app can use. Since `v1` is the default, you'll usually want at least that one defined.

#### app_id.api.subItems

If your API consists of multiple APIs you can list them in here it has the same signature as `{app_id.api}`.

#### app_id.api.apiName

If your API is accessible on oher URL than `/api/{app_id}/{versions[0]}/openapi.json` you can change this by passing correct name, the URL will look like `/api/{apiName}/{versions[0]}/openapi.json`

### Frontend Properties

The following properties are used if your app has a frontend:

#### app_id.frontend.title

If you want the name of your app to appear differently on the frontend, set this property to override it.

#### app_id.frontend.app_base

If you want this app to use the same codebase as another existing app, set this value to the ID of that app.

#### app_id.frontend.module

To indicate chrome how to load the application for federated modules you need to pass this property. It can either be a magic link containing `yourApp#./RootApp` for most applications. If you want to be more specific you can pass in module object containing `appName`, `scope` and `module`

##### app_id.frontend.module.appName

To indicate chrome loader from what app to load your fed-mods config.

##### app_id.frontend.module.scope

To indicate federated modules scope of your application (you can have multiple scopes per one app). This is usually your application's name (same as `appName`).

##### app_id.frontend.module.module

To indicate which module should be loaded when rendering your app (you can have multiple modules per one scope). This is usually `./RootApp`

##### app_id.frontend.module.group

If you have first level application to indicate which group should be managed by this module.

#### app_id.frontend.paths

This is the list of URL paths where your app will be located.

#### app_id.frontend.sub_apps

If your app is a parent to any other apps, those apps should be listed here. Also, if your app has a parent app, or is listed under one of the top-level bundles (e.g. Insights, RHEL, Hybrid), you should add your app to the appropriate sub_apps list.

Here are some notes on defining the items in sub_apps:

- If you specify the title field, the sub-app will be self-contained, and it will not look up the app's ID elsewhere in the config.
- If the title is specified, the sub-app's path will be determined by its ID.
- If the title is not specified, the ID will be used to find the app's details in the rest of the config.

#### app_id.frontend.reload

If your app will be located under some other app, but isn't managed by that app, you can use this property to override the automatic generation of the URL.
This property is commonly used for Settings apps, and tells Chrome's navigation the actual URL of your app.

#### app_id.frontend.suppress_id

This property is used if the app isn't a real app on disk, and only exists for navigation purposes. This removes the app ID on the frontend so that the nav bar works as expected.

### Other Optional Properties

The following properties aren't required for all apps, but may still apply to your app:

#### app_id.channel

This is the ID of the slack channel on ansible.slack.com that you want automatic notifications to be posted to.

#### app_id.description

This is a description of your app's purpose or functionalities, which is used by some other apps.

#### app_id.disabled_on_prod

Setting this value to `true` will disable the app from deploying to Prod (and appearing in Prod). This applies to both `stable` and `beta` releases.

#### app_id.docs

This is the link to your app's documentation.

#### app_id.source_repo

This is the URL of the development (not deployment) repo for your app, i.e. the one you commit to.

#### app_id.mailing_list

This is the mailing list associated with your project. Used to automate email notifications.

#### app_id.top_level

If this is set to `true`, your app will be a top-level app, which is usually reserved for bundles (Insights, RHEL, Hybrid, Openshift, etc).
Use this if your app does not have a parent app or bundle.

#### permissions.method

If you want to hide any navigational element based on some chrome's logic, this is the right property. This defines the function to be used in order to hide nav item. (Chrome's list of methods)[https://github.com/RedHatInsights/insights-chrome#permissions].

#### permissions.args

If the `permissions.method` requires some arguments in order to properly work, this is how to pass them to it: an array of items.

#### permissions.apps

If you want to control visibility for multiple navigation items you can specify one permission per entry and list which apps from `frontend.sub_apps` should be checked.

## Akamai API Access

Before you can run the property-updating script locally, you need to have access to the Akamai API.
To do this, follow the steps located [here](https://developer.akamai.com/api/getting-started). In step 5 of this doc the guide instructs you to set the Access Level of the Diagnostics Tools API to READ_WRITE; do this but also set the Access Level of the Property Manager API (PAPI) to READ-Write. Otherwise you will not have authorization to the configurations of Cloud Services. Make sure that the `.edgerc` file you create is located in your `home` directory and has the credentials defined in the `[default]` section of the file.
If you're able to run the sample call at the end of the doc, you should be able to run the script. If you run into issues, there may be something wrong with your `.edgerc` file.

For more information on the Akamai API, read the [property manager docs](https://developer.akamai.com/api/core_features/property_manager/v1.html).

## Build Process

This repository has a webhook that automatically builds a [Jenkins job](https://jenkins-jenkins.5a9f.insights-dev.openshiftapps.com/job/akamai-config-deployer/) on every push. To configure this webhook, check the project's [webhook settings](https://github.com/RedHatInsights/cloud-services-config/settings/hooks)

## Testing your changes locally

Testing local changes is straightforward. First, add a line like this to your insights-proxy spandx config:

```diff
--- a/profiles/local-frontend.js
+++ b/profiles/local-frontend.js
@@ -9,5 +9,6 @@ routes[`/beta/${SECTION}/${APP_ID}`] = { host: `http://localhost:${FRONTEND_PORT
 routes[`/${SECTION}/${APP_ID}`]      = { host: `http://localhost:${FRONTEND_PORT}` };
 routes[`/beta/apps/${APP_ID}`]       = { host: `http://localhost:${FRONTEND_PORT}` };
 routes[`/apps/${APP_ID}`]            = { host: `http://localhost:${FRONTEND_PORT}` };
+routes[`/beta/config`]            = { host: `http://localhost:8889` };

 module.exports = { routes };
```

Restart your insights-proxy to pick up the change.

Create a `beta/config` directory inside of `cloud-services-config` and copy `main.yml` to it. Then, from the `cloud-services-config` dir, run `npx http-server -p 8889`. In your browser, go to `https://ci.foo.redhat.com:1337/beta/rhel/dashboard`. You should see something logged like this from npx:

```text
$ npx http-server -p 8889
npx: installed 25 in 2.484s
Starting up http-server, serving ./
Available on:
  http://127.0.0.1:8889
  http://192.168.0.25:8889
  http://10.10.122.158:8889
Hit CTRL-C to stop the server
[Tue Nov 05 2019 09:50:55 GMT-0500 (Eastern Standard Time)] "GET /beta/config/main.yml" "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:69.0) Gecko/20100
101 Firefox/69.0"
```

Before you go developing, make sure you can make a simple change and see it in the web UI. Try renaming "Dashboard" to "XDashboardX". To do this, make an edit to `main.yml` similar to this (make sure you are editing the one in `beta/config`):

```diff
diff --git a/main.yml b/main.yml
index 090fd7e..a680d06 100644
--- a/main.yml
+++ b/main.yml
@@ -152,7 +152,7 @@ cost-management:
   mailing_list: cost-mgmt@redhat.com

 dashboard:
-  title: Dashboard
+  title: XDashboardX
   channel: '#flip-mode-squad'
   deployment_repo: https://github.com/RedHatInsights/insights-dashboard-build
   frontend:
```

Then, reload the site. You may not see your change at this point! Try clearing your local storage in your browser. To do this in Firefox, hit Shift-F9 and click "Local Storage", then right click on <https://ci.foo.redhat.com:1337> and delete all. Refresh the page and you should then see your changes. You'll notice too that SimpleHTTPServer logged another request. You will need to repeat this cache clearing step whenever you make changes to `main.yml` in your local environment.
