const { ethers } = require("ethers");
const axios = require("axios");

// Flashbots Relay Endpoint (Mainnet)
const FLASHBOTS_RELAY = "https://relay.flashbots.net";
// Additional Builders for maximum inclusion
const BUILDERS = [
    "https://relay.flashbots.net",
    "https://rpc.beaverbuild.org",
    "https://rpc.titanbuilder.xyz",
    "https://builder0x69.io"
];

class BundleExecutor {
    constructor(provider, signer, authSigner) {
        this.provider = provider;
        this.signer = signer; // The bot executing the trade
        this.authSigner = authSigner; // Flashbots auth (can be random wallet)
    }

    /**
     * Submit a transaction as a private bundle
     * @param {Object} transaction - The populated transaction object
     * @param {number} targetBlock - Block number to target
     */
    async submitBundle(transaction, targetBlock) {
        console.log(`🛡️ Preparing Flashbots Bundle for Block ${targetBlock}...`);

        // 1. Sign the transaction
        const signedTx = await this.signer.signTransaction(transaction);

        // 2. Construct the Bundle
        // A bundle can contain multiple txs. Here we just send ours.
        // We could also add a "bribe" tx if needed.
        const bundle = [
            {
                tx: signedTx,
                canRevert: false
            }
        ];

        // 3. Simulate Bundle (Safety Check)
        const simulation = await this.simulateBundle(bundle, targetBlock);
        if (simulation.error) {
            console.error(`❌ Bundle Simulation Failed: ${simulation.error.message}`);
            return { success: false, error: simulation.error };
        }
        console.log(`✅ Bundle Simulation Successful. Gas Used: ${simulation.gasUsed}`);

        // 4. Submit to All Builders
        const promises = BUILDERS.map(builderUrl =>
            this.sendToBuilder(builderUrl, bundle, targetBlock)
        );

        const results = await Promise.allSettled(promises);
        const successful = results.filter(r => r.status === 'fulfilled' && r.value.success).length;

        console.log(`🚀 Bundle submitted to ${successful}/${BUILDERS.length} builders`);
        return { success: true, bundleHash: simulation.bundleHash };
    }

    /**
     * Simulate the bundle via Flashbots RPC
     */
    async simulateBundle(bundle, targetBlock) {
        const payload = {
            jsonrpc: "2.0",
            id: 1,
            method: "eth_callBundle",
            params: [
                {
                    txs: bundle.map(b => b.tx),
                    blockNumber: "0x" + targetBlock.toString(16),
                    stateBlockNumber: "latest"
                }
            ]
        };

        const signature = await this.signFlashbotsHeader(payload);

        try {
            const response = await axios.post(FLASHBOTS_RELAY, payload, {
                headers: {
                    'X-Flashbots-Signature': signature,
                    'Content-Type': 'application/json'
                }
            });

            if (response.data.error) {
                return { error: response.data.error };
            }

            return {
                success: true,
                gasUsed: response.data.result.results[0].gasUsed,
                bundleHash: response.data.result.bundleHash
            };
        } catch (error) {
            return { error: error };
        }
    }

    /**
     * Send bundle to a specific builder
     */
    async sendToBuilder(builderUrl, bundle, targetBlock) {
        const payload = {
            jsonrpc: "2.0",
            id: 1,
            method: "eth_sendBundle",
            params: [
                {
                    txs: bundle.map(b => b.tx),
                    blockNumber: "0x" + targetBlock.toString(16),
                }
            ]
        };

        const signature = await this.signFlashbotsHeader(payload);

        try {
            await axios.post(builderUrl, payload, {
                headers: {
                    'X-Flashbots-Signature': signature,
                    'Content-Type': 'application/json'
                }
            });
            return { success: true };
        } catch (error) {
            // console.warn(`Failed to send to ${builderUrl}`);
            return { success: false };
        }
    }

    /**
     * Sign the payload for Flashbots Auth
     * header: X-Flashbots-Signature: <address>:<signature>
     */
    async signFlashbotsHeader(payload) {
        const body = JSON.stringify(payload);
        const digest = ethers.id(body);
        const signature = await this.authSigner.signMessage(ethers.getBytes(digest));
        return `${await this.authSigner.getAddress()}:${signature}`;
    }
}

module.exports = { BundleExecutor };
