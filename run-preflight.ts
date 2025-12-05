import { runPreflightChecks } from './services/preflightService.ts';

runPreflightChecks()
    .then(result => {
        console.log(JSON.stringify(result, null, 2));
    })
    .catch(err => {
        console.error('Error running preflight:', err);
    });
