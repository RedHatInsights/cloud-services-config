const Joi = require('joi');

const permissionsSchema = Joi.object({
  method: Joi.string().required(),
  apps: Joi.array().items(Joi.string()),
  args: Joi.array().items(Joi.any())
})

const routeSchema = Joi.object({
  appId: Joi.string().when('isExternal', {
    is: Joi.exist(),
    then: Joi.forbidden(),
    otherwise: Joi.required()
  }),
  title: Joi.string().required(),
  href: Joi.string().required(),
  permissions: Joi.array().items(permissionsSchema),
  isExternal: Joi.bool()
})

const navItemSchema = Joi.object({
  appId: Joi.string().when('href', {
    is: Joi.exist(),
    then: Joi.required(),
    otherwise: Joi.forbidden(),
  }),
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
  })
})

const subNavItem = navItemSchema.fork(['groupId', 'navItems', 'appId', 'icon'], schema => schema.forbidden())

const navigationSchema = Joi.object({
  id: Joi.string().required(),
  title: Joi.string().required(),
  navItems: Joi.array().items(navItemSchema).required()
}).shared(subNavItem.id('subNavItem'));

module.exports = navigationSchema;
