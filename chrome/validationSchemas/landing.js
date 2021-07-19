const Joi = require('joi')

const landingItemSchema = Joi.object({
  title: Joi.string().required(),
  href: Joi.string().required(),
  id: Joi.string().required(),
})

const landingSchema = Joi.array().items(landingItemSchema);

module.exports = landingSchema;