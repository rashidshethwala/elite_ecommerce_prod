#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Building React + Vite frontend..."

# Install dependencies
echo "📦 Installing dependencies..."
npm ci

# Build the project
echo "🔨 Building project..."
npm run build

echo "✅ Frontend build complete!"
echo "📁 Build files are in the 'dist' directory"