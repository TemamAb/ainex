.PHONY: all bot contract test

all: contract bot

contract:
@echo "Building Contracts..."
cd contracts && forge build

bot:
@echo "Building Rust Bot..."
cd bot && cargo build --release

test:
@echo "Running Simulation..."
cd contracts && forge test -vvv
