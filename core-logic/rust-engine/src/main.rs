use ethers::prelude::*;
use ethers::providers::{Provider, Ws};
use std::sync::Arc;
use dotenv::dotenv;
use std::env;
use anyhow::Result;

// ApexFlashAggregator Address (Deployed)
const AGGREGATOR_ADDRESS: &str = "0x82BBAA3B0982D88741B275aE1752DB85CAfe3c65";

abigen!(
    ApexFlashAggregator,
    r#"[
        function executeArbitrage(address token, uint256 amount, bytes calldata data) external
        function owner() view returns (address)
    ]"#
);

#[tokio::main]
async fn main() -> Result<()> {
    dotenv().ok();
    env_logger::init();

    println!("🚀 AINEX RUST ENGINE: INITIALIZING...");

    let rpc_url = env::var("ETH_RPC_URL").unwrap_or_else(|_| "ws://localhost:8545".to_string());
    println!("🔌 Connecting to: {}", rpc_url);

    let provider = Provider::<Ws>::connect(rpc_url).await?;
    let client = Arc::new(provider);

    let address: Address = AGGREGATOR_ADDRESS.parse()?;
    let contract = ApexFlashAggregator::new(address, client.clone());

    println!("✅ Connected to ApexFlashAggregator at {:?}", address);
    println!("🎧 Listening for new blocks...");

    let mut stream = client.subscribe_blocks().await?;

    while let Some(block) = stream.next().await {
        println!("📦 New Block: {:?} | Timestamp: {}", block.number.unwrap(), block.timestamp);
        
        // HIGH-FREQUENCY LOGIC HERE
        // 1. Scan mempool (not implemented in this basic loop)
        // 2. Check for arb opportunities
        // 3. Execute via contract
        
        // Mock Execution Trigger
        if block.timestamp % 100 < 5 { // 5% chance per block
            println!("⚡ Opportunity Detected! Executing Strategy...");
            // In a real scenario, we would construct the payload and call executeArbitrage
            // let tx = contract.execute_arbitrage(...);
            // tx.send().await?;
        }
    }

    Ok(())
}
