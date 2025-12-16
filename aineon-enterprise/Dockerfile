FROM node:18-alpine

WORKDIR /app

# Copy dependencies first for caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Expose the application port
EXPOSE 3000

# Start command
CMD ["npm", "start"]
