# Chrome navigation schema

```TS
/**
 * Rules to show/hide link in a navigation
 * @see https://github.com/RedHatInsights/insights-chrome/blob/master/docs/navigation.md#permissions
*/
type Permissions = any

interface Route = {
  /**
   * Name of an Application module.
  */
  appId: string
  /**
   * Link title
  */
  title: string
  /**
   * Link pathname
   * Must be an absolute path to the module
   * @example "/insights/advisor/recommendations"
  */
  href: string
  /**
   * Link will redirect user to beta env
  */
  isBeta?: boolean;
  permissions?: Permissions[]
  /**
   * Marks an external link. The browser will open a new tab.
   * @default false
   * You must include the origin for external routes
   * @example href: "https://www.google.com/"
  */
  isExternal?: boolean;
  /**
   * Flag to controlling link visibility in application filter
   * @default true
   * @example filterable: false
  */
  filterable?: boolean;
}

interface NavItem {
  /**
   * Indicate if the navigation Item has a second level
   * @default false
  */
  expandable?: boolean
  /**
   * Name of an Application module.
   * Required if "expandable" is not true
  */
  appId?: string
  /**
   * Nav item title
  */
  title: string
  /**
   * Top-level link
   * Required if "expandable" is not true
  */
  href?: string
  /**
   * Nested links
   * Required if "expandable" is true
  */
  routes?: Route[]
  permissions?: Permissions[]
  /**
   * Flag to controlling link visibility in application filter
   * @default true
   * @example filterable: false
  */
  filterable?: boolean;
}

interface GroupItem {
  /**
   * Id of the group
  */
  groupId: string
  /**
   * Group title
  */
  title: string
  /**
   * Icon before title
  */
  icon?: 'wrench' | 'trend-up' | 'shield'
  /**
   * Items of the group
  */
  navItems: NavItem[]
}

interface NavigationSchema {
  id: string
  /**
   * Title of the navigation segment
  */
  title: string
  /**
   * Navigation items
  */
  navItems: (GroupItem | NavItem)[]
}
```