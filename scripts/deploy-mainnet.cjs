const hre = require("hardhat");

async function main() {
    console.log("🚀 DEPLOYING AINEX TO ETHEREUM MAINNET...\n");

    // Get deployer account
    const [deployer] = await hre.ethers.getSigners();
    console.log("Deploying with account:", deployer.address);
    console.log("Account balance:", (await hre.ethers.provider.getBalance(deployer.address)).toString());

    // Mainnet Addresses
    const AAVE_POOL_PROVIDER = "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e";
    const BALANCER_VAULT = "0xBA12222222228d8Ba445958a75a0704d566BF2C8";

    console.log("\n📝 Deploying ApexFlashAggregator...");
    const ApexFlashAggregator = await hre.ethers.getContractFactory("ApexFlashAggregator");
    const aggregator = await ApexFlashAggregator.deploy(AAVE_POOL_PROVIDER, BALANCER_VAULT);

    await aggregator.waitForDeployment();
    const aggregatorAddress = await aggregator.getAddress();

    console.log("✅ ApexFlashAggregator deployed to:", aggregatorAddress);

    console.log("\n⏳ Waiting for block confirmations...");
    await aggregator.deploymentTransaction().wait(5);

    console.log("\n🔍 Verifying on Etherscan...");
    try {
        await hre.run("verify:verify", {
            address: aggregatorAddress,
            constructorArguments: [AAVE_POOL_PROVIDER, BALANCER_VAULT],
        });
        console.log("✅ Contract verified on Etherscan");
    } catch (error) {
        console.log("⚠️  Verification failed:", error.message);
    }

    console.log("\n🎯 DEPLOYMENT COMPLETE!");
    console.log("Contract Address:", aggregatorAddress);
    console.log("Etherscan:", `https://etherscan.io/address/${aggregatorAddress}`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
