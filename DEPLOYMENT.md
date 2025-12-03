# Deploying Ainex to Vercel

This guide will help you deploy the Ainex dashboard to the Vercel platform.

## Prerequisites

1.  A [Vercel Account](https://vercel.com/signup).
2.  This project pushed to a GitHub repository.

## Deployment Steps

1.  **Login to Vercel**: Go to [vercel.com](https://vercel.com) and log in.
2.  **Add New Project**: Click "Add New..." -> "Project".
3.  **Import Repository**: Find your `ainex` repository in the list and click "Import".
4.  **Configure Project**:
    *   **Framework Preset**: Ensure "Next.js" is selected.
    *   **Root Directory**: `./` (default).
    *   **Build Command**: `next build` (default).
    *   **Output Directory**: `.next` (default).
5.  **Environment Variables**:
    *   Expand the "Environment Variables" section.
    *   Add the following variables (copy values from your local `.env` file or use the ones below):
        *   `NEXT_PUBLIC_RPC_URL_ETHEREUM`: `https://eth.llamarpc.com` (or your private RPC)
        *   `NEXT_PUBLIC_RPC_URL_ARBITRUM`: `https://arbitrum.llamarpc.com`
        *   `NEXT_PUBLIC_RPC_URL_BASE`: `https://base.llamarpc.com`
        *   `ETHERSCAN_API_KEY`: Your Etherscan API Key
        *   `ARBISCAN_API_KEY`: Your Arbiscan API Key
        *   `BASESCAN_API_KEY`: Your Basescan API Key
6.  **Deploy**: Click the "Deploy" button.

## Post-Deployment

*   Vercel will build your project and assign a domain (e.g., `ainex-dashboard.vercel.app`).
*   You can verify the deployment by visiting the URL.
*   **Note**: Since this is a client-side dashboard interacting with the blockchain, it runs entirely in the user's browser. The server side is only used for serving the static assets.

## Troubleshooting

*   **Build Errors**: Check the "Logs" tab in Vercel to see any build errors.
*   **Missing Env Vars**: If features aren't working, verify you added the Environment Variables correctly in the Project Settings.
