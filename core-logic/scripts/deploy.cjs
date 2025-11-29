const hre = require("hardhat");

// NETWORK CONFIGURATION
const CONFIG = {
  // Ethereum Mainnet (and Hardhat Fork)
  "hardhat": {
    aaveProvider: "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e",
    balancerVault: "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
  },
  "localhost": {
    aaveProvider: "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e",
    balancerVault: "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
  },
  // Arbitrum One
  "arbitrum": {
    aaveProvider: "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb",
    balancerVault: "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
  },
  // Optimism
  "optimism": {
    aaveProvider: "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb",
    balancerVault: "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
  },
  // Base
  "base": {
    aaveProvider: "0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D",
    balancerVault: "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
  }
};

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const networkName = hre.network.name;

  console.log(`\n==========================================`);
  console.log(`🚀 DEPLOYING TO: ${networkName.toUpperCase()}`);
  console.log(`📜 Deployer: ${deployer.address}`);
  console.log(`==========================================\n`);

  // Get Network Config
  const config = CONFIG[networkName];
  if (!config) {
    throw new Error(`❌ No config found for network: ${networkName}`);
  }

  console.log(`[1/2] Deploying ApexDEXRouter...`);
  const ApexDEXRouter = await hre.ethers.getContractFactory("ApexDEXRouter");
  const dexRouter = await ApexDEXRouter.deploy();
  await dexRouter.waitForDeployment();
  console.log(`✅ ApexDEXRouter deployed to: ${await dexRouter.getAddress()}`);

  console.log(`\n[2/2] Deploying ApexFlashAggregator...`);
  console.log(`   - Aave Provider: ${config.aaveProvider}`);
  console.log(`   - Balancer Vault: ${config.balancerVault}`);

  const ApexFlashAggregator = await hre.ethers.getContractFactory("ApexFlashAggregator");
  const flashAggregator = await ApexFlashAggregator.deploy(
    config.aaveProvider,
    config.balancerVault
  );
  await flashAggregator.waitForDeployment();
  console.log(`✅ ApexFlashAggregator deployed to: ${await flashAggregator.getAddress()}`);

  console.log(`\n==========================================`);
  console.log(`   ✅ SUCCESS: DEPLOYMENT COMPLETE`);
  console.log(`==========================================\n`);

  console.log(`Deployed Contracts:`);
  console.log(`  - ApexDEXRouter: ${await dexRouter.getAddress()}`);
  console.log(`  - ApexFlashAggregator: ${await flashAggregator.getAddress()}`);
}

main().catch((error) => {
  console.error("\n❌ Deployment failed:");
  console.error(error);
  process.exitCode = 1;
});
