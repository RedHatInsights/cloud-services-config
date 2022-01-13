const Joi = require('joi')

const routeModuleSchema = Joi.object({
  id: Joi.string().required(),
  dynamic: Joi.boolean(),
  module: Joi.string().when('routes', {
    is: Joi.array().has(Joi.object({
      dynamic: Joi.alternatives().try(Joi.valid(false), Joi.forbidden())
    })),
    then: Joi.required(),
  }).when('dynamic', {
    is: false,
    then: Joi.forbidden(),
    break: true,
  }).when('routes', {
    is: Joi.array().has(Joi.string()),
    then: Joi.required(),
    break: true,
  }).when('routes', {
    is: Joi.array().has(Joi.object({
      pathname: Joi.any(),
      exact: Joi.any(),
      dynamic: Joi.alternatives().try(Joi.boolean().valid(true), Joi.forbidden()),
      isFedramp: Joi.boolean(),
    })),
    then: Joi.required(),
  }),
  routes: Joi.array().items(Joi.alternatives().try(Joi.string(), Joi.object({
    pathname: Joi.string().required(),
    exact: Joi.boolean(),
    dynamic: Joi.boolean(),
    isFedramp: Joi.boolean(),
  }))).required()
})

const moduleItemSchema = Joi.object({
  dynamic: Joi.boolean().optional(),
  isFedramp: Joi.boolean(),
  defaultDocumentTitle: Joi.string().optional(),
  manifestLocation: Joi.alternatives().conditional('dynamic', {
    is: false,
    then: Joi.any().forbidden(),
    otherwise: Joi.string().required()
  }),
  modules: Joi.array().items(routeModuleSchema).required()
})

const modulesSchema = Joi.object().pattern(Joi.string(), moduleItemSchema);

module.exports = modulesSchema;