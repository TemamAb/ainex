import axios from 'axios';

// REAL-TIME PRICE SERVICE
// Fetches actual market data to drive the Ainex Engine analysis
// STRICTLY NO MOCK DATA PER USER PROTOCOL

interface PriceData {
    ethereum: { usd: number };
    arbitrum: { usd: number };
    base: { usd: number }; // using ethereum as proxy if base token not indexed uniquely in free tier
}

let lastPrice: PriceData | null = null;
let lastUpdate = 0;
const CACHE_DURATION = 30000; // 30 seconds

export const getRealPrices = async (): Promise<PriceData> => {
    // Return cached if fresh
    if (lastPrice && Date.now() - lastUpdate < CACHE_DURATION) {
        return lastPrice;
    }

    try {
        console.log('Fetching real-time prices from Coingecko...');
        const response = await axios.get('https://api.coingecko.com/api/v3/simple/price', {
            params: {
                ids: 'ethereum,arbitrum',
                vs_currencies: 'usd'
            },
            timeout: 5000
        });

        const data = response.data;

        lastPrice = {
            ethereum: { usd: data.ethereum?.usd || 0 },
            arbitrum: { usd: data.arbitrum?.usd || 0 },
            base: { usd: data.ethereum?.usd || 0 } // Base usually pegged to ETH for gas, using ETH as proxy for simplicity
        };
        lastUpdate = Date.now();

        return lastPrice;
    } catch (error) {
        console.warn('Real-time price fetch failed, using fallback/last known:', error);
        if (lastPrice) return lastPrice;

        // Final fallback if API completely down - returns 0 to indicate "No Data" rather than Mock Data
        return {
            ethereum: { usd: 0 },
            arbitrum: { usd: 0 },
            base: { usd: 0 }
        };
    }
};
