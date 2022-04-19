const Joi = require('joi');
const { navItemSchema } = require('./navigation');

const landingSchema = Joi.array().items(navItemSchema);

module.exports = landingSchema;