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
    })),
    then: Joi.required(),
  }),
  routes: Joi.array().items(Joi.alternatives().try(Joi.string(), Joi.object({
    pathname: Joi.string().required(),
    exact: Joi.boolean(),
    dynamic: Joi.boolean(),
    isFedramp: Joi.boolean()
  }))).required()
})

const moduleItemSchema = Joi.object({
  dynamic: Joi.boolean().optional(),
  defaultDocumentTitle: Joi.string().optional(),
  manifestLocation: Joi.alternatives().conditional('dynamic', {
    is: false,
    then: Joi.any().forbidden(),
    otherwise: Joi.string().required()
  }),
  isFedramp: Joi.boolean(),
  modules: Joi.array().items(routeModuleSchema).required(),
  analytics: Joi.object({
    APIKey: Joi.string().required()
  }),
  config: Joi.object(),
  fullProfile: Joi.boolean().optional()
})

const modulesSchema = Joi.object().pattern(Joi.string().token(), moduleItemSchema);

module.exports = modulesSchema;
