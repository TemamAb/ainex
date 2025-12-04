# Use a lightweight Node.js image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files first (optimized for caching)
COPY package*.json ./

RUN npm install

# Accept build arguments for Next.js public vars
ARG NEXT_PUBLIC_ETH_RPC_URL
ARG NEXT_PUBLIC_ARBITRUM_RPC_URL
ARG NEXT_PUBLIC_BASE_RPC_URL
ARG NEXT_PUBLIC_ETH_WS_URL

# Copy the rest of the application code
COPY . .

# Build the Next.js application
RUN npm run build

# Expose the listening port
EXPOSE 3000

# Start the application
CMD ["npx", "next", "start"]