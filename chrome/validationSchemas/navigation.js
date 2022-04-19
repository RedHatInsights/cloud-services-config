const Joi = require('joi');

const permissionsSchema = Joi.object({
  method: Joi.string().required(),
  apps: Joi.array().items(Joi.string()),
  args: Joi.array().items(Joi.any())
})

const routeSchema = Joi.object({
  appId: Joi.string().token().when('isExternal', {
    is: Joi.exist(),
    then: Joi.forbidden(),
    otherwise: Joi.required()
  }),
  filterable: Joi.bool(),
  isBeta: Joi.bool(),
  title: Joi.string().required(),
  href: Joi.string().required(),
  permissions: Joi.array().items(permissionsSchema),
  isExternal: Joi.bool(),
  product: Joi.string(),
  notifier: Joi.string()
})

const navItemSchema = Joi.object({
  appId: Joi.string().token()
  .when('isExternal', {
    is: Joi.exist(),
    then: Joi.optional(),
    break: true,
  })
  .when('href', {
    is: Joi.exist(),
    then: Joi.required(),
    otherwise: Joi.forbidden(),
  }),
  isHidden: Joi.bool(),
  filterable: Joi.bool(),
  isExternal: Joi.bool(),
  title: Joi.string().required(),
  groupId: Joi.string(),
  href: Joi.string().when('expandable', {
    is: true,
    then: Joi.forbidden(),
    break: true
  }).when('groupId', {
    not: Joi.exist(),
    then: Joi.required(),
    otherwise: Joi.optional()
  }),
  expandable: Joi.bool().optional(),
  routes: Joi.array().items(routeSchema).when('expandable', {
    is: true,
    then: Joi.required(),
    otherwise: Joi.forbidden()
  }),
  icon: Joi.string().when('groupId', {
    not: Joi.exist(),
    then: Joi.forbidden(),
    otherwise: Joi.optional().valid('wrench', 'trend-up', 'shield')
  }),
  navItems: Joi.alternatives().conditional('groupId', {
    is: Joi.exist(),
    then: Joi.array().items(Joi.link('#subNavItem')).required(),
    otherwise: Joi.forbidden()
  }),
  permissions: Joi.array().items(permissionsSchema).when('groupId', {
    is: Joi.exist(),
    then: Joi.forbidden(),
    otherwise: Joi.optional()
  }),
  product: Joi.string(),
  notifier: Joi.string(),
  id: Joi.string().optional()
})

const subNavItem = navItemSchema.fork(['groupId', 'navItems', 'appId', 'icon'], schema => schema.forbidden())

const navigationSchema = Joi.object({
  id: Joi.string().required(),
  title: Joi.string().required(),
  navItems: Joi.array().items(navItemSchema).required()
}).shared(subNavItem.id('subNavItem'));

module.exports.navItemSchema = navItemSchema

module.exports.navigationSchema = navigationSchema;
