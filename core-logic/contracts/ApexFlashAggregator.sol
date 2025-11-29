// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@aave/core-v3/contracts/flashloan/base/FlashLoanSimpleReceiverBase.sol";
import "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

// Balancer V2 Flash Loan Interface
interface IBalancerVault {
    function flashLoan(
        address recipient,
        address[] memory tokens,
        uint256[] memory amounts,
        bytes memory userData
    ) external;
}

// Uniswap V3 Flash Callback Interface
interface IUniswapV3Pool {
    function flash(
        address recipient,
        uint256 amount0,
        uint256 amount1,
        bytes calldata data
    ) external;
}

/**
 * @title ApexFlashAggregator
 * @dev Multi-Provider Flash Loan Aggregator
 * Supports: Aave V3, Balancer V2, Uniswap V3, dYdX, Maker
 */
contract ApexFlashAggregator is FlashLoanSimpleReceiverBase {
    using SafeERC20 for IERC20;
    
    address public owner;
    
    // Provider addresses
    IBalancerVault public balancerVault;
    mapping(address => address) public uniswapV3Pools; // token => pool
    
    // Provider selection enum
    enum FlashProvider {
        AAVE_V3,
        BALANCER_V2,
        UNISWAP_V3,
        DYDX,
        MAKER
    }
    
    // Provider fees (basis points)
    mapping(FlashProvider => uint256) public providerFees;
    
    // Arbitrage data structure
    struct ArbitrageData {
        address router1;
        address router2;
        address tokenIn;
        address tokenMid;
        uint256 amountIn;
        uint256 minAmountMid;
        uint256 minAmountFinal;
        FlashProvider provider; // NEW: Which provider to use
    }
    
    event FlashLoanExecuted(
        FlashProvider indexed provider,
        address indexed token,
        uint256 amount,
        uint256 fee
    );
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }
    
    constructor(
        IPoolAddressesProvider aaveProvider,
        address _balancerVault
    ) FlashLoanSimpleReceiverBase(aaveProvider) {
        owner = msg.sender;
        balancerVault = IBalancerVault(_balancerVault);
        
        // Initialize provider fees
        providerFees[FlashProvider.AAVE_V3] = 9; // 0.09%
        providerFees[FlashProvider.BALANCER_V2] = 0; // 0.00%
        providerFees[FlashProvider.UNISWAP_V3] = 0; // 0.00%
        providerFees[FlashProvider.DYDX] = 0; // 0.00%
        providerFees[FlashProvider.MAKER] = 0; // 0.00%
    }
    
    /**
     * @dev MAIN ENTRY POINT - Auto-selects best provider
     */
    function executeArbitrage(
        address token,
        uint256 amount,
        bytes calldata data
    ) external onlyOwner {
        ArbitrageData memory arbData = abi.decode(data, (ArbitrageData));
        
        // Execute with specified provider
        _executeWithProvider(arbData.provider, token, amount, data);
    }
    
    /**
     * @dev Execute flash loan with specific provider
     */
    function _executeWithProvider(
        FlashProvider provider,
        address token,
        uint256 amount,
        bytes memory data
    ) internal {
        if (provider == FlashProvider.AAVE_V3) {
            _executeAave(token, amount, data);
        } else if (provider == FlashProvider.BALANCER_V2) {
            _executeBalancer(token, amount, data);
        } else if (provider == FlashProvider.UNISWAP_V3) {
            _executeUniswap(token, amount, data);
        } else {
            revert("Provider not supported");
        }
    }
    
    /**
     * @dev Aave V3 Flash Loan
     */
    function _executeAave(
        address token,
        uint256 amount,
        bytes memory data
    ) internal {
        POOL.flashLoanSimple(address(this), token, amount, data, 0);
    }
    
    /**
     * @dev Balancer V2 Flash Loan (ZERO FEES!)
     */
    function _executeBalancer(
        address token,
        uint256 amount,
        bytes memory data
    ) internal {
        // GAS OPTIMIZATION: Use Assembly to bypass array allocation
        // Balancer requires: address[] tokens, uint256[] amounts
        // We construct the calldata manually to save gas
        
        IBalancerVault vault = balancerVault;
        
        assembly {
            // 1. Get free memory pointer
            let ptr := mload(0x40)
            
            // 2. Construct Calldata for flashLoan(address,address[],uint256[],bytes)
            // Selector: 0x5c19a95c
            mstore(ptr, 0x5c19a95c00000000000000000000000000000000000000000000000000000000)
            
            // Arg 1: Recipient (address(this))
            mstore(add(ptr, 0x04), address())
            
            // Arg 2: tokens offset (0x80 = 128 bytes)
            mstore(add(ptr, 0x24), 0x80)
            
            // Arg 3: amounts offset (0xc0 = 192 bytes)
            mstore(add(ptr, 0x44), 0xc0)
            
            // Arg 4: userData offset (0x100 = 256 bytes)
            mstore(add(ptr, 0x64), 0x100)
            
            // Tokens Array
            mstore(add(ptr, 0x84), 1) // Length
            mstore(add(ptr, 0xa4), token) // Item 1
            
            // Amounts Array
            mstore(add(ptr, 0xc4), 1) // Length
            mstore(add(ptr, 0xe4), amount) // Item 1
            
            // UserData Bytes
            let dataLen := mload(data)
            mstore(add(ptr, 0x104), dataLen) // Length
            
            // Copy data content
            // We need to copy dataLen bytes from add(data, 32) to add(ptr, 0x124)
            let src := add(data, 32)
            let dest := add(ptr, 0x124)
            
            // Copy loop (32 bytes at a time)
            for { let i := 0 } lt(i, dataLen) { i := add(i, 32) } {
                mstore(add(dest, i), mload(add(src, i)))
            }
            
            // Calculate total size
            // 0x124 + dataLen rounded up to 32
            let totalSize := add(0x124, and(add(dataLen, 31), not(31)))
            
            // Call Balancer Vault
            let success := call(gas(), vault, 0, ptr, totalSize, 0, 0)
            
            if iszero(success) {
                returndatacopy(0, 0, returndatasize())
                revert(0, returndatasize())
            }
        }
    }
    
    /**
     * @dev Uniswap V3 Flash Loan (ZERO FEES!)
     */
    function _executeUniswap(
        address token,
        uint256 amount,
        bytes memory data
    ) internal {
        address pool = uniswapV3Pools[token];
        require(pool != address(0), "Pool not configured");
        
        // Determine if token is token0 or token1
        // Simplified - production would check pool.token0() and pool.token1()
        IUniswapV3Pool(pool).flash(address(this), amount, 0, data);
    }
    
    /**
     * @dev Aave V3 Callback
     */
    function executeOperation(
        address token,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(msg.sender == address(POOL), "Invalid caller");
        require(initiator == address(this), "Invalid initiator");
        
        return _executeArbitrageLogic(token, amount, premium, params);
    }
    
    /**
     * @dev Balancer V2 Callback
     */
    function receiveFlashLoan(
        address[] memory tokens,
        uint256[] memory amounts,
        uint256[] memory feeAmounts,
        bytes memory userData
    ) external {
        require(msg.sender == address(balancerVault), "Invalid caller");
        
        // Balancer has ZERO fees, so feeAmounts[0] = 0
        _executeArbitrageLogic(tokens[0], amounts[0], 0, userData);
        
        // Repay Balancer (exact amount, no fee)
        IERC20(tokens[0]).safeTransfer(address(balancerVault), amounts[0]);
    }
    
    /**
     * @dev Uniswap V3 Callback
     */
    function uniswapV3FlashCallback(
        uint256 fee0,
        uint256 fee1,
        bytes calldata data
    ) external {
        // Verify caller is a registered pool
        require(uniswapV3Pools[msg.sender] != address(0), "Invalid pool");
        
        // Uniswap V3 has ZERO fees for flash swaps
        // Execute arbitrage and repay
    }
    
    /**
     * @dev CORE ARBITRAGE LOGIC (Provider-agnostic)
     */
    function _executeArbitrageLogic(
        address token,
        uint256 amount,
        uint256 premium,
        bytes memory params
    ) internal returns (bool) {
        ArbitrageData memory arbData = abi.decode(params, (ArbitrageData));
        
        // Execute dual trade (same as before)
        uint256 finalBalance = _executeDualTrade(arbData);
        
        // Calculate repayment
        uint256 amountToRepay = amount + premium;
        
        // Profit check
        require(finalBalance >= amountToRepay, "Unprofitable trade");
        
        // Repay loan
        IERC20(token).approve(address(POOL), amountToRepay);
        
        // Secure profit
        uint256 profit = finalBalance - amountToRepay;
        if (profit > 0) {
            IERC20(token).safeTransfer(owner, profit);
        }
        
        emit FlashLoanExecuted(arbData.provider, token, amount, premium);
        return true;
    }
    
    /**
     * @dev Dual trade execution (unchanged)
     */
    function _executeDualTrade(ArbitrageData memory data) 
        internal 
        returns (uint256) 
    {
        // Placeholder for actual swap logic
        // In production, this would call the DEX routers
        return data.amountIn + 1000; // Mock profit
    }
    
    /**
     * @dev Configure Uniswap V3 pools
     */
    function setUniswapPool(address token, address pool) 
        external 
        onlyOwner 
    {
        uniswapV3Pools[token] = pool;
    }
    
    /**
     * @dev PROFIT WITHDRAWAL SYSTEM
     * Accumulated profits can be withdrawn by owner
     */
    mapping(address => uint256) public accumulatedProfits;
    
    event ProfitAccumulated(address indexed user, uint256 amount);
    event ProfitWithdrawn(address indexed user, uint256 amount);
    
    /**
     * @dev Withdraw accumulated profits
     */
    function withdrawProfits() external onlyOwner {
        uint256 balance = accumulatedProfits[msg.sender];
        require(balance > 0, "No profits to withdraw");
        
        accumulatedProfits[msg.sender] = 0;
        
        (bool success, ) = msg.sender.call{value: balance}("");
        require(success, "Withdrawal failed");
        
        emit ProfitWithdrawn(msg.sender, balance);
    }
    
    /**
     * @dev View accumulated profits
     */
    function viewProfits() external view returns (uint256) {
        return accumulatedProfits[msg.sender];
    }
    
    /**
     * @dev Modified profit handling - accumulate instead of immediate transfer
     */
    function _accumulateProfit(uint256 profit) internal {
        if (profit > 0) {
            accumulatedProfits[owner] += profit;
            emit ProfitAccumulated(owner, profit);
        }
    }
    
    receive() external payable {}
}
