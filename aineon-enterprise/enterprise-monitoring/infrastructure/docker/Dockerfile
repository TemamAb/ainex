FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY backend-api/package*.json ./backend-api/

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

FROM node:18-alpine

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Copy built application
COPY --from=builder --chown=nodejs:nodejs /app .

USER nodejs

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => {if (r.statusCode === 200) process.exit(0); process.exit(1)}).on('error', () => process.exit(1))"

# Expose ports
EXPOSE 3000 8081

# Start command
CMD ["node", "backend-api/server.js"]
