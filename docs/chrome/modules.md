# Chrome UI modules schema definition

```TS
/**
 * Route of a UI module
*/
interface ConfigurableRoute {
  /**
   * Absolute pathname to module
  */
  pathname: string
  /**
   * Exactly match pathname
   * @default false
   * If set to true, the route will ignore any nested routes.
   * Useful if a chrome namespace has a landing page module. 
  */
  exact?: boolean
  /**
   * Is the route ready for a client-side navigation
   * @default true
   * If set to false, before accessing or after leaving a module the chrome will perform a full page refresh.
   * Useful, if module did not adopt chrome 2
  */
  dynamic?: boolean
}

type Route = string | ConfigurableRoute

/**
 * Application module definition.
 * Module defines on what module and on which routes it should be rendered.
*/
interface Module {
  /**
   * Unique module ID
   */
  id: string
  /**
   * Name of the federated module with the application entry.
   * Default webpack configuration sets this to "./RootApp"
   * This attribute is mutually exclusive with the "dynamic" attribute,
  */
  module?: string
  /**
   * Is the whole module ready for client-side navigation.
   * Attribute cannot be set to false if "module" attribute was set
   * @default true
   * If set to false, before accessing or after leaving a module the chrome will perform a full page refresh.
   * Useful, if module did not adopt chrome 2
   * 
  */
  dynamic?: boolean,
  /**
   * Routes on which current module should be rendered
  */
  routes: Route[]
}

interface ApplicationModule {
  /**
   * Pathname to the "fed-mods.json" file generated during the build.
   * Only required if an application was already migrated to chrome 2
  */
  manifestLocation?: string
  /**
   * Is the whole application ready for a client-side navigation.
   * @default trueIf set to false, before accessing or after leaving any application module the chrome will perform a full page refresh.
  */
  dynamic?: boolean;
  modules: Module[]
}

interface ModulesSchema {
  [key: string] ApplicationModule
}
```