const Joi = require('joi');

module.exports = Joi.array().items(Joi.object({
  id: Joi.string().required(),
  description: Joi.string(),
  icon: Joi.string(),
  title: Joi.string().required(),
  links: Joi.alternatives().try(Joi.string(), Joi.object({
    isExternal: Joi.bool().required(),
    href: Joi.string().required(),
    title: Joi.string().required(),
    description: Joi.string(),
  })).required()
}));
