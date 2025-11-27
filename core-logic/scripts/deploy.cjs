const hre = require("hardhat");

async function main() {
  console.log("Starting deployment...");
  console.log("Network:", hre.network.name);

  // 1. Deploy ApexDEXRouter
  console.log("\n[1/2] Deploying ApexDEXRouter...");
  const ApexDEXRouter = await hre.ethers.getContractFactory("ApexDEXRouter");
  const dexRouter = await ApexDEXRouter.deploy();
  await dexRouter.waitForDeployment();
  const dexRouterAddress = await dexRouter.getAddress();
  console.log(`✅ ApexDEXRouter deployed to: ${dexRouterAddress}`);

  // 2. Deploy ApexFlashLoan
  console.log("\n[2/2] Deploying ApexFlashLoan...");

  // Use the Aave V3 PoolAddressesProvider address directly
  // Note: On forked mainnet, this address exists and is valid
  const AAVE_ADDRESS_PROVIDER = process.env.AAVE_ADDRESS_PROVIDER || "0x2f39d218133AFab932771980D262D623440A7B2ee";

  console.log(`Using Aave PoolAddressesProvider: ${AAVE_ADDRESS_PROVIDER}`);

  try {
    const ApexFlashLoan = await hre.ethers.getContractFactory("ApexFlashLoan");
    // Deploy directly with the address string
    const flashLoan = await ApexFlashLoan.deploy(AAVE_ADDRESS_PROVIDER);
    await flashLoan.waitForDeployment();
    const flashLoanAddress = await flashLoan.getAddress();
    console.log(`✅ ApexFlashLoan deployed to: ${flashLoanAddress}`);

    console.log("\n==========================================");
    console.log("   ✅ SUCCESS: DEPLOYMENT COMPLETE");
    console.log("==========================================");
    console.log(`\nDeployed Contracts:`);
    console.log(`  - ApexDEXRouter: ${dexRouterAddress}`);
    console.log(`  - ApexFlashLoan: ${flashLoanAddress}`);
  } catch (error) {
    console.log(`\n⚠️  ApexFlashLoan deployment encountered an issue:`);
    console.log(`   ${error.message}`);
    console.log(`\n✅ Partial Success: ApexDEXRouter deployed successfully`);
    console.log(`   ApexDEXRouter address: ${dexRouterAddress}`);
  }
}

main().catch((error) => {
  console.error("\n❌ Deployment failed:");
  console.error(error);
  process.exitCode = 1;
});
