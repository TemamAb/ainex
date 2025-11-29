#!/bin/bash
# Render Build Script for AiNex Dashboard
# This ensures all dependencies are installed and the app is built for production

echo "🚀 Starting AiNex Render Build Process..."

# Step 1: Install dependencies
echo "📦 Installing Node dependencies..."
npm install --legacy-peer-deps || npm install

# Step 2: Build the application
echo "🔨 Building application..."
npm run build

# Step 3: Verify build output
if [ -d "dist" ]; then
  echo "✅ Build successful! Output directory: dist/"
  ls -lh dist/
else
  echo "❌ Build failed - no dist directory found"
  exit 1
fi

echo "✅ Build process complete!"
