// DEX Contract ABIs and Addresses

// Uniswap V3 Router
export const UNISWAP_V3_ROUTER_ABI = [
    'function exactInputSingle((address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 deadline, uint256 amountIn, uint256 amountOutMinimum, uint160 sqrtPriceLimitX96)) external payable returns (uint256 amountOut)',
    'function exactOutputSingle((address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 deadline, uint256 amountOut, uint256 amountInMaximum, uint160 sqrtPriceLimitX96)) external payable returns (uint256 amountIn)',
];

// Uniswap V3 Quoter
export const UNISWAP_V3_QUOTER_ABI = [
    'function quoteExactInputSingle(address tokenIn, address tokenOut, uint24 fee, uint256 amountIn, uint160 sqrtPriceLimitX96) external returns (uint256 amountOut)',
];

// Aave V3 Pool
export const AAVE_V3_POOL_ABI = [
    'function flashLoan(address receiverAddress, address[] calldata assets, uint256[] calldata amounts, uint256[] calldata modes, address onBehalfOf, bytes calldata params, uint16 referralCode) external',
    'function getReserveData(address asset) external view returns (tuple(uint256 configuration, uint128 liquidityIndex, uint128 currentLiquidityRate, uint128 variableBorrowIndex, uint128 currentVariableBorrowRate, uint128 currentStableBorrowRate, uint40 lastUpdateTimestamp, uint16 id, address aTokenAddress, address stableDebtTokenAddress, address variableDebtTokenAddress, address interestRateStrategyAddress, uint128 accruedToTreasury, uint128 unbacked, uint128 isolationModeTotalDebt))',
];

// ERC20 Token ABI (minimal)
export const ERC20_ABI = [
    'function balanceOf(address owner) view returns (uint256)',
    'function decimals() view returns (uint8)',
    'function symbol() view returns (string)',
    'function approve(address spender, uint256 amount) returns (bool)',
    'function allowance(address owner, address spender) view returns (uint256)',
];

// Contract Addresses by Chain
export const CONTRACT_ADDRESSES = {
    ethereum: {
        uniswapV3Router: '0xE592427A0AEce92De3Edee1F18E0157C05861564',
        uniswapV3Quoter: '0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6',
        aaveV3Pool: '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2',
        weth: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        usdc: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        usdt: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    },
    arbitrum: {
        uniswapV3Router: '0xE592427A0AEce92De3Edee1F18E0157C05861564',
        uniswapV3Quoter: '0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6',
        aaveV3Pool: '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
        weth: '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
        usdc: '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
        usdt: '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
    },
    base: {
        uniswapV3Router: '0x2626664c2603336E57B271c5C0b26F421741e481',
        uniswapV3Quoter: '0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a',
        aaveV3Pool: '0xA238Dd80C259a72e81d7e4664a9801593F98d1c5',
        weth: '0x4200000000000000000000000000000000000006',
        usdc: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
    },
};

// Common token pairs for arbitrage
export const TRADING_PAIRS = [
    { token0: 'WETH', token1: 'USDC' },
    { token0: 'WETH', token1: 'USDT' },
    { token0: 'WBTC', token1: 'USDC' },
    { token0: 'WBTC', token1: 'WETH' },
];
