# Chrome navigation configuration

Specification of each configuration file can be found here:
- [fed-modules.json](https://github.com/RedHatInsights/cloud-services-config/blob/ci-beta/docs/chrome/modules.md)
- [landing-navigation.json](https://github.com/RedHatInsights/cloud-services-config/blob/ci-beta/docs/chrome/landing.md)
- [<namespace>-navigation.json](https://github.com/RedHatInsights/cloud-services-config/blob/ci-beta/docs/chrome/navigation.md)

Each schema is validated in the CI by its validators. You can run the validation via `npm run validate-chrome` in the repository root.

**NOTE**: The deployment information still has to be present in the [main.yml](https://github.com/RedHatInsights/cloud-services-config#adding-config-for-new-apps).

## Prerequisites
- Application UI repositories are setup.
- The deployment configuration is present in the [main.yml](https://github.com/RedHatInsights/cloud-services-config#adding-config-for-new-apps) configuration. You can ignore the `sub_apps` and any configurations from the `frontend` object tied to the left nav. The `paths` key is still required for Akamai to serve static assets properly!

## **NOTE**: configuration bellow applies to applications using chrome 2 rendering

### How do I know my application is using chrome 2 rendering?
- Your application is using `@redhat-cloud-services/frontend-components-config` **version 4+** webpack config
-  Your application config uses the module federation plugin `@redhat-cloud-services/frontend-components-config/federated-modules.js`.
- Your application **does not use the `skipChrome2` flag**.

[Example configuration](https://github.com/RedHatInsights/frontend-starter-app/blob/master/config/prod.webpack.config.js)

To migrate to chrome 2 rendering, follow the [guide](https://github.com/RedHatInsights/insights-chrome/blob/master/docs/migrationGuide.md) or contact the plat-ex team.

## Registering new module (app) to chrome

To add a new module following configuration must be done:

1. Go to the `/chrome/fed-modules.json` file.
2. Add a value under a specific key to the object.
    - The key must be equal to the `insights.appname` from `package.json` in your repository
    - **NOTE**: if your `appname` includes the *dash* `-` character, **the convert the key to camel case** (required due to webpack container naming limitations). For example: `user-preferences` -> `userPreferences`.
3. Add a federated modules `manifestLocation` of your application. With default build config the path is `/apps/<insights.appname>/fed-modules.json`

```json
{
  "userPreferences": {
    "manifestLocation": "/apps/user-preferences/fed-mods.json"
  }
}
```
4. Add the `modules` definition of your application. A module defines what federated module will be used as an application entry point and on which routes it should be rendered.

```json
{
    "userPreferences": {
        "manifestLocation": "/apps/user-preferences/fed-mods.json",
        "modules": [
            {
                "id": "user-preferences-email",
                "module": "./RootApp",
                "routes": [
                    "/user-preferences",
                    "/user-preferences/email"
                ]
            },
            {
                "id": "user-preferences-notifications",
                "module": "./OtherModule",
                "routes": [
                    "/user-preferences/notifications"
                ]
            }
        ]
    },
}
```

The above configuration will setup the following:
- New UI application called `userPreferences` is now avaiable in chrome.
- Application modules metadata can be found at `/apps/user-preferences/fed-mods.json`.
- Application will render two modules
- `user-preferences-email` will be rendered at `/user-preferences` and `/user-preferences/email` and will use the `./RootApp` federated as the entry point.
- `user-preferences-notifications` will be rendered at `/user-preferences/notifications` and will use `OtherModule` as an entry point.

**NOTE**: The `./RootApp` is a default entry module name of the [common config package](https://github.com/RedHatInsights/frontend-components/tree/master/packages/config).

## Render existing application on a new route

If we want to render existing application on a new route, simply add a new route to the module list:

```diff
  "routes": [
      "/user-preferences",
-     "/user-preferences/email"
+     "/user-preferences/email",
+     "/insights/email"
  ]

```

## **NOTE**: configuration bellow applies to applications not using chrome 2 rendering
If the application is not using the chrome 2 rendering it has set the `dynamic` property to `false`. It also cannot include any federated modules meta-data.

Application not using chrome 2 rendering will not benefit from any chrome 2 features, like client-side routing between different applications, dependency sharing, performance improvements, etc.

```diff
{
    "userPreferences": {
-       "manifestLocation": "/apps/user-preferences/fed-mods.json",
+       "dynamic": false,
        "modules": [
            {
                "id": "user-preferences-email",
-               "module": "./RootApp",
                "routes": [
                    "/user-preferences",
                    "/user-preferences/email"
                ]
            },
            {
                "id": "user-preferences-notifications",
-               "module": "./OtherModule",
                "routes": [
                    "/user-preferences/notifications"
                ]
            }
        ]
    },
}
```

## **NOTE**: configuration bellow applies to all applications

## <a name="top-level"></a>Adding a new top-level link to the chrome left navigation

### Prerequisites
- UI is registered as a module in the `fed-modules.json` file.

1. Open a correct navigation schema file. Navigation files are located at `chrome/<namespace>-navigation.json`. For example, if we want to add a new link to `/insights`, modify the `chrome/rhel-navigation.json`.
2. Add new link entry to the schema:

```diff
diff --git a/chrome/rhel-navigation.json b/chrome/rhel-navigation.json
index ad62a21..63445cb 100644
--- a/chrome/rhel-navigation.json
+++ b/chrome/rhel-navigation.json
@@ -7,6 +7,11 @@
             "title": "Dashboard",
             "href": "/insights/dashboard"
         },
+        {
+            "appId": "userPreferences",
+            "title": "New top level link",
+            "href": "/insights/user-preferences/email"
+        },
         {
             "groupId": "operations",
             "title": "Operations Insights",

```

The above example will do the following.
- Adds a new link between the `Dashboard` and `Operations Insights` entries.
- Link will lead to a module with `userPreferences` id.
- Link destination is set to `/insights/user-preferences/email`

**NOTE**: The `href` must be an absolute path! Relative paths are not accepted.

## <a name="nested-link"></a> Adding an expandable section with sub-links to the chrome left navigation

### Prerequisites
- UI is registered as a module in the `fed-modules.json` file.
- Add a [top level link](#top-level) entry.
- Omit the `href` attribute

1. Add `expandable` flag to the entry

```diff
{
    "appId": "userPreferences",
    "title": "New top level link",
-   "href": "/insights/user-preferences/email"
+   "expandable": true
}
```
2. Add `routes` array to the entry

```diff
{
    "appId": "userPreferences",
    "title": "New top level link",
    "expandable": true,
+   "routes": []
}
```
3. Add a nested link(s) into the `routes` array,
```diff
{
    "appId": "userPreferences",
    "title": "New top level link",
    "expandable": true,
-   "routes": []
+   "routes": [
+     {
+       "appId": "userPreferences",
+       "title": "Email",
+       "href": "/insights/user-preferences/email"
+     }
+   ]
}
```

## Adding a group to the left navigation

Navigation groups are named sections of the navigation. Group has an extra title and can have an icon next to the group title.

1. Add a new group into the `navItems` navigation attribute.
```diff
diff --git a/chrome/rhel-navigation.json b/chrome/rhel-navigation.json
index ad62a21..17dcf2d 100644
--- a/chrome/rhel-navigation.json
+++ b/chrome/rhel-navigation.json
@@ -7,6 +7,12 @@
             "title": "Dashboard",
             "href": "/insights/dashboard"
         },
+        {
+            "groupId": "operations",
+            "title": "Operations Insights",
+            "icon": "wrench",
+            "navItems": []
+        },
         {

```
2. Add navigation entries to the `navItems` array. Follow the [top level](#top-level) or [nested links](#nested-link) guides.

## Adding an external link to the left navigation.

External links will open a new tab in the browser. External links are commonly used to open documentation or support pages outside of the Red Hat cloud platform.

1. Add a new top-level or nested link with external flag property.

```diff
+{
+    "title": "Red Hat",
+    "isExternal": true,
+    "href": "https://www.redhat.com/"
+},
```

## Removing a link from the application filter

By default, top-level links are also visible in the application filter. If a link does not directly lead to an application (such as an external documentation link), you can remove the link from the application filter by setting `filterable` flag.

```diff
{
    "title": "Red Hat",
    "isExternal": true,
+   "filterable": false,    
    "href": "https://www.redhat.com/"
},
```
