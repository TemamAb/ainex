FROM node:18-alpine
WORKDIR /app
# Copy package.json
COPY package.json ./
# Install dependencies
RUN npm install --production=false
# Copy application source
COPY . .
# Build Vite app
RUN npm run build
# Runtime
ENV NODE_ENV=production
ENV HOSTNAME="0.0.0.0"
EXPOSE 3000
CMD ["npm", "start"]
