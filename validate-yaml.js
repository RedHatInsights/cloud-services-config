const fs = require('fs');
const {load} = require('js-yaml');
const Joi = require('joi');

const permissionsSchema = Joi.object({
    method: Joi.string().required(),
    apps: Joi.array().items(Joi.string()),
    args: Joi.array().items(Joi.any())
})

const frontendSchema = Joi.object({
    title: Joi.string(),
    reload: Joi.string(),
    paths: Joi.array().items(Joi.string()),
    sub_apps: Joi.array().items(Joi.object({
        id: Joi.string().required().allow(''),
        default: Joi.boolean(),
        title: Joi.string(),
        group: Joi.string(),
        reload: Joi.string(),
        permissions: permissionsSchema
    }))
})

const schema = Joi.object({
    disabled_on_prod: Joi.boolean(),
    description: Joi.string(),
    docs: Joi.string(),
    mailing_list: Joi.string(),
    title: Joi.string(),
    api: Joi.object({
        apiName: Joi.string(),
        versions: [Joi.array().items(Joi.string()), Joi.string()],
        isBeta: Joi.boolean(),
        alias: Joi.array().items(Joi.string()),
        subItems: Joi.object().pattern(/^/ ,Joi.object({
            versions: [Joi.array().items(Joi.string()), Joi.string()],
            title: Joi.string()
        })),
        tags: Joi.array().items(Joi.object({
            value: Joi.string().required(),
            title: Joi.string().required()
        }))
    }),
    channel: Joi.string(),
    deployment_repo: Joi.string(),
    source_repo: Joi.string(),
    frontend: frontendSchema,
    top_level: Joi.boolean(),
    permissions: permissionsSchema
})

const inputfile = 'main.yml';
const structure = load(fs.readFileSync(inputfile, { encoding: 'utf-8' }));



async function validate() {
    Object.entries(structure).forEach(async ([ key, value ]) => {
        try {
            const result = await schema.validateAsync(value);
        } catch (error) {
            console.error(`Erro in ${key} app definition.\n`, error)
            process.exit(1)
        }
    })
}

validate()
