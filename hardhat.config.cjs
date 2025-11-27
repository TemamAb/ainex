require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config(); // Loads environment variables from a .env file

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.19", // Matches the pragma in ApexFlashLoan.sol
  networks: {
    hardhat: {
      // Configures the local network to fork Ethereum Mainnet
      forking: {
        // CRITICAL: Ensure ALCHEMY_MAINNET_URL is set in your .env file
        // Fallback to ETH_RPC_URL or a public RPC for build verification
        url: (process.env.ALCHEMY_MAINNET_URL && process.env.ALCHEMY_MAINNET_URL.length > 0) ? process.env.ALCHEMY_MAINNET_URL : ((process.env.ETH_RPC_URL && process.env.ETH_RPC_URL.length > 0) ? process.env.ETH_RPC_URL : "https://eth.llamarpc.com"),
        // Using a fixed block number ensures repeatable testing results
        blockNumber: 19000000
      }
    }
  },
  paths: {
    sources: "./core-logic/contracts",
    tests: "./core-logic/tests",
    cache: "./cache",
    artifacts: "./artifacts"
  },
  etherscan: {
    // Requires ETHERSCAN_API_KEY to be set in .env for verification
    apiKey: process.env.ETHERSCAN_API_KEY
  }
};
