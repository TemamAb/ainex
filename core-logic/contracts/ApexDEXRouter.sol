// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title ApexDEXRouter
 * @dev Unified router for multiple DEX interactions
 * Supports Uniswap V2/V3, Sushiswap, and other major DEXs
 */
contract ApexDEXRouter {
    using SafeERC20 for IERC20;
    
    address public owner;
    
    // DEX router addresses
    address public constant UNISWAP_V2_ROUTER = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address public constant UNISWAP_V3_ROUTER = 0xE592427A0AEce92De3Edee1F18E0157C05861564;
    address public constant SUSHISWAP_ROUTER = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;
    
    event SwapExecuted(
        address indexed dex,
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 amountIn,
        uint256 amountOut
    );
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    /**
     * @dev Execute swap on specified DEX
     */
    function swapExactInput(
        address dexRouter,
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 minAmountOut,
        address recipient
    ) external onlyOwner returns (uint256 amountOut) {
        // Transfer tokens to this contract first
        IERC20(tokenIn).safeTransferFrom(msg.sender, address(this), amountIn);
        
        // Approve router to spend tokens
        IERC20(tokenIn).safeApprove(dexRouter, amountIn);
        
        // Execute swap based on DEX type
        if (dexRouter == UNISWAP_V2_ROUTER) {
            amountOut = _swapUniswapV2(tokenIn, tokenOut, amountIn, minAmountOut, recipient);
        } else if (dexRouter == UNISWAP_V3_ROUTER) {
            amountOut = _swapUniswapV3(tokenIn, tokenOut, amountIn, minAmountOut, recipient);
        } else if (dexRouter == SUSHISWAP_ROUTER) {
            amountOut = _swapSushiswap(tokenIn, tokenOut, amountIn, minAmountOut, recipient);
        } else {
            revert("Unsupported DEX");
        }
        
        require(amountOut >= minAmountOut, "Insufficient output");
        emit SwapExecuted(dexRouter, tokenIn, tokenOut, amountIn, amountOut);
        
        return amountOut;
    }
    
    
    /**
     * @dev Execute Uniswap V2 swap
     */
    function _swapUniswapV2(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 minAmountOut,
        address recipient
    ) internal returns (uint256) {
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;

        // Approve router
        IERC20(tokenIn).safeApprove(UNISWAP_V2_ROUTER, amountIn);

        uint[] memory amounts = IUniswapV2Router02(UNISWAP_V2_ROUTER).swapExactTokensForTokens(
            amountIn,
            minAmountOut,
            path,
            recipient,
            block.timestamp
        );
        
        return amounts[amounts.length - 1];
    }
    
    /**
     * @dev Execute Uniswap V3 swap
     */
    function _swapUniswapV3(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 minAmountOut,
        address recipient
    ) internal returns (uint256) {
        // For this fix, we will revert as V3 requires more complex params (fee tier etc)
        // and we want to ensure safety over broken mock logic.
        revert("Uniswap V3 not yet implemented");
    }
    
    /**
     * @dev Execute Sushiswap swap
     */
    function _swapSushiswap(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 minAmountOut,
        address recipient
    ) internal returns (uint256) {
        // SushiSwap is V2 compatible
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;

        IERC20(tokenIn).safeApprove(SUSHISWAP_ROUTER, amountIn);

        uint[] memory amounts = IUniswapV2Router02(SUSHISWAP_ROUTER).swapExactTokensForTokens(
            amountIn,
            minAmountOut,
            path,
            recipient,
            block.timestamp
        );
        
        return amounts[amounts.length - 1];
    }
    
    /**
     * @dev Emergency token withdrawal
     */
    function emergencyWithdraw(address token, uint256 amount) external onlyOwner {
        IERC20(token).safeTransfer(owner, amount);
    }
}

interface IUniswapV2Router02 {
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);
}
