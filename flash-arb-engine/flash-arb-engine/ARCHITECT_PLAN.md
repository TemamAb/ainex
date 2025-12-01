# Institutional Arbitrage Engine - Master Plan

## Phase 1: The Vault (Smart Contracts)
- [ ] Initialize Foundry project (`forge init`).
- [ ] Create `FlashLoanReceiver.sol` inheriting Aave V3 `IFlashLoanSimpleReceiver`.
- [ ] Implement `executeOperation`:
    - Logic: Receive Asset -> Swap on UniV3 -> Swap on Sushi -> Repay Loan.
    - Safety: `require(balanceAfter > balanceBefore + premium)`.
- [ ] Write `test/ArbSimulator.t.sol` to fork Mainnet and mock a profitable spread.

## Phase 2: The Sentinel (Rust Bot)
- [ ] Initialize Rust project (`cargo new bot`).
- [ ] Dependencies: `ethers` (or `alloy`), `tokio`, `dotenv`, `reqwest`.
- [ ] Implement `PriceFeed`: Listen to UniV3 Pool Events via WSS.
- [ ] Implement `OpportunityCalculator`: Real-time calculation of (Spread - Gas).

## Phase 3: The Bundler (MEV Execution)
- [ ] Add `ethers-flashbots` dependency.
- [ ] Create `BundleSigner`: Wrap transaction + Bribe (Miner Tip).
- [ ] Simulation: Dry-run bundle against Flashbots simulation RPC before sending.

## Phase 4: Dashboard & Deployment
- [ ] Create a TUI (Text User Interface) in Rust for live profit tracking.
- [ ] Deployment scripts for Mainnet.
