const express = require('express');
const app = express();

const MODE = process.env.APP_MODE || 'sim';
const PROFIT = process.env.PROFIT_MODE === '1';

app.get('/mode/status', (req,res) => {
  res.json({
    mode: MODE,
    profit: PROFIT,
    blockchainReady: false,
    marketReady: false
  });
});

app.get('/', (req,res) => res.send('<h1>AINEX Dashboard running safely</h1>'));

const PORT = process.env.PORT || 8000;
app.listen(PORT, '0.0.0.0', () => console.log(`Server running on port ${PORT}, mode=${MODE}`));
