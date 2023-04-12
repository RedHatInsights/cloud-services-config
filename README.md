# :exclamation: This repo is no longer used a source of config files for HCC! :exclamation:

Due to ongoing migration to the frontend operator, module and navigation files were moved to te chrome service api. Follow this [link](https://github.com/RedHatInsights/chrome-service-backend/blob/main/docs/cloud-services-config.md) to learn more.


# About

This repo deals with the high-level configuration of Cloud Services. `main.yml` contains the source of truth for CS apps, and the `akamai` folder deals with updating our Akamai configuration.

## Branch links and syncing

These are the urls for each branch:

### Beta
* ci-beta -> https://ci.console.redhat.com/beta
* qa-beta -> https://qa.console.redhat.com/beta
* stage-beta -> https://console.stage.redhat.com/beta
* prod-beta -> https://console.redhat.com/beta

### Stable
* ci-stable -> https://ci.console.redhat.com
* qa-stable -> https://qa.console.redhat.com
* stage -> https://console.stage.redhat.com
* prod-stable -> https://console.redhat.com

These branches sync:

* ci-beta -> qa-beta -> stage-beta
* ci-stable -> qa-stable -> stage-stable

## Adding Config for New Apps

To enable a new app in our environments, you need to create configuration for it in `main.yml` and in `/chrome` directory. After that create a PR to merge it into the `ci-beta` branch. The configuration for the non-prod beta branches is kept in sync. Changes to `ci-beta` will automatically be merged into `qa-beta` (as mentioned above).

When you need this config added to another environment (`prod-beta`, `ci-stable`, `qa-stable`, `prod-stable`), please open another PR for that environment. If you have any concerns about this process, feel free to ping #forum-clouddot-ui on Slack for assistance.

Here is some example configuration that demonstrates the structure, using all required and optional properties:

### `main.yml`

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
        paths:
            - /example/path
            - /another/example/path
    source_repo: https://github.com/app-development-repo-url
    mailing_list: app-title@redhat.com
```

### `/chrome/fed-modules.json`

Add new application metadata to chrome modules registry.

[More details](https://github.com/RedHatInsights/cloud-services-config/blob/ci-beta/docs/chrome/docs.md#registering-new-module-app-to-chrome)

```js
{
    /** app-id must be the same as in the main.yml file */
    "<app-id>": {
        "manifestLocation": "/apps/<app-id>/fed-mods.json",
        "modules": [
            {
                "id": "module identifier",
                "module": "./RootApp",
                "routes": [
                    "/example/path",
                    "/another/example/path"
                ]
            }
        ]
    }
}
```
### `/chrome/<bundle>-navigation.json`

Add a new link to chrome navigation files. The navigation registry file is based on application location within the chrome application. For example, if the application should live under `/settings` route, modify the `settings-navigation.json` file.

[More details](https://github.com/RedHatInsights/cloud-services-config/blob/ci-beta/docs/chrome/docs.md#adding-a-new-top-level-link-to-the-chrome-left-navigation)

```js
{
    /** app-id must be the same as in the main.yml file */
    "appId": "<app-id>",
    /** Title of the link in browser */
    "title": "App title",
    /** Exact URL path to the application. Can be a nested route. */
    "href": "/settings/new-app"
}
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

If your API consists of multiple APIs, you can list them here. Each has the same signature as `{app_id.api}`.

#### app_id.api.apiName

If your API is accessible on a URL other than `/api/{app_id}/{versions[0]}/openapi.json`, you can change it by passing the correct name. The URL will look like `/api/{apiName}/{versions[0]}/openapi.json`

### Frontend Properties

The following properties are used if your app has a frontend:

#### app_id.frontend.title

If you want the name of your app to appear differently on the frontend, set this property to override it.

#### app_id.frontend.app_base

If you want this app to use the same codebase as another existing app, set this value to the ID of that app.

#### app_id.frontend.paths

This is the list of URL paths where your app will be located.

### Other Optional Properties

The following properties aren't required for all apps, but may still apply to your app:

#### app_id.productId

The Red Hat product ID for your application. This is tied to fields on Portal Case Management for pre-filling information.

#### app_id.infoId

Some applications are mounted in two locations, but use the same base repo (ex. RBAC and MUA), in this case MUA needs to point to RBAC's app.info.json, so this is the base app for that url.

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

Create a `beta/config` directory inside of `cloud-services-config` and crate a sym link (or copy) to `/chrome` directory in it. Then, from the `cloud-services-config` dir, run `npx http-server -p 8889`. In your browser, go to `https://ci.foo.redhat.com:1337/beta/rhel/dashboard`. You should see something logged like this from npx:

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

Before you go developing, make sure you can make a simple change and see it in the web UI. Try renaming "Dashboard" link title to "XDashboardX" in `/chrome/rhel-navigation.json`.

```diff
diff --git a/chrome/rhel-navigation.json b/chrome/rhel-navigation.json
index 67237cc..4485daa 100644
--- a/chrome/rhel-navigation.json
+++ b/chrome/rhel-navigation.json
@@ -4,7 +4,7 @@
     "navItems": [
         {
             "appId": "dashboard",
-            "title": "Dashboard",
+            "title": "XDashboardX",
             "filterable": false,
             "href": "/insights/dashboard",
             "product": "Red Hat Insights"

```

Now go to `/insights/dashboard`. You may not see your navigation change at this point! Try clearing your local storage in your browser. To do this in Firefox, hit Shift-F9 and click "Local Storage", then right click on <https://ci.foo.redhat.com:1337> and delete all. Refresh the page and you should then see your changes. You'll notice too that SimpleHTTPServer logged another request.
