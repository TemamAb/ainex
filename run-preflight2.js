const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '.env') });
require('ts-node').register({ transpileOnly: true, esm: true });
const { runPreflightChecks } = require('./services/preflightService.ts');

runPreflightChecks()
    .then(result => {
        console.log(JSON.stringify(result, null, 2));
    })
    .catch(err => {
        console.error('Error running preflight:', err);
    });
