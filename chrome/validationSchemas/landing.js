const Joi = require('joi');
const { navItemSchema, subNavItem } = require('./navigation');

const landingSchema = Joi.array().items(navItemSchema).shared(subNavItem.id('subNavItem'));

module.exports = landingSchema;
