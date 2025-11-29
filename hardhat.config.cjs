require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config(); // Loads environment variables from a .env file

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.19", // Matches the pragma in ApexFlashLoan.sol
  networks: {
    hardhat: {
      forking: {
        url: (process.env.ALCHEMY_MAINNET_URL && process.env.ALCHEMY_MAINNET_URL.length > 0) ? process.env.ALCHEMY_MAINNET_URL : ((process.env.ETH_RPC_URL && process.env.ETH_RPC_URL.length > 0) ? process.env.ETH_RPC_URL : "https://eth.llamarpc.com"),
        blockNumber: 19000000
      }
    },
    mainnet: {
      url: process.env.ETH_RPC_URL || "https://eth.llamarpc.com",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    },
    arbitrum: {
      url: process.env.ARBITRUM_RPC_URL || "https://arb1.arbitrum.io/rpc",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    },
    optimism: {
      url: process.env.OPTIMISM_RPC_URL || "https://mainnet.optimism.io",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    },
    base: {
      url: process.env.BASE_RPC_URL || "https://mainnet.base.org",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
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
