#!/bin/bash

# Exit on error
set -e

echo "🚀 Setting up Crawl4AI API for Hugging Face Spaces"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install --with-deps chromium

# Set up environment
echo "🔧 Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from template. Please edit it with your API keys."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p data

# Set permissions
echo "🔒 Setting permissions..."
chmod +x setup.sh

echo "✅ Setup complete! You can now run the server with:"
echo "   supervisord -c supervisord.conf"
echo "   or"
echo "   python app.py"