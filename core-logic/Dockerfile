# Use Node.js 18 as the base image
FROM node:18-bullseye

# Install Python (for your AI agents) and build tools
RUN apt-get update && apt-get install -y     python3     python3-pip     build-essential     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definitions
COPY package.json ./

# Install Node dependencies
RUN npm install

# Copy the rest of the engine code
COPY . .

# Expose the port (if your command-center uses one)
EXPOSE 3000

# Start the Engine
# Note: We use the path relative to core-logic root
CMD ["node", "platform/command-center.js"]
