require('ts-node').register({ transpileOnly: true });
const { runPreflightChecks } = require('./services/preflightService');

runPreflightChecks()
    .then(result => {
        console.log(JSON.stringify(result, null, 2));
    })
    .catch(err => {
        console.error('Error running preflight:', err);
    });
