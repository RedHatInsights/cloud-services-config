const fs = require('fs');
const path = require('path');
const landingSchema = require('./validationSchemas/landing');
const modulesSchema = require('./validationSchemas/modules');
const { navigationSchema } = require('./validationSchemas/navigation');



const navigationFiles = fs.readdirSync(__dirname)
  .filter(f => f.endsWith('-navigation.json') && f !== 'landing-navigation.json');
const landingFile = path.resolve(__dirname, 'landing-navigation.json');
const modulesFile = path.resolve(__dirname, 'fed-modules.json');


async function validateLanding() {    
  try {
    const file = fs.readFileSync(landingFile, 'utf-8');
    await landingSchema.strict(true).validateAsync(JSON.parse(file));
  } catch (error) {
    console.error(`Error in landing page navigation definition.\n`, error);
    process.exit(1);
  }
}

async function validateModules() {
  try {
    const file = fs.readFileSync(modulesFile, 'utf-8');
    await modulesSchema.strict(true).validateAsync(JSON.parse(file));
  } catch (error) {
    console.error(`Error in federated modules definition.\n`, error);
    process.exit(1);
  }
}

async function validateNavigation() {
  navigationFiles.forEach(async fileName => {
    const file = fs.readFileSync(path.join(__dirname, fileName), 'utf-8');
    try {
      const result = await navigationSchema.strict(true).validateAsync(JSON.parse(file));
    } catch (error) {
      console.error(`Error in ${fileName} navigation definition.\n`, error);
      process.exit(1);
    }
  })
}

validateLanding()
validateModules()
validateNavigation()