#!/bin/bash

# Exit on error
set -e

echo "🚀 Setting up Crawl4AI API for Hugging Face Spaces"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Set up environment
echo "🔧 Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from template."
fi

echo "✅ Setup complete! The server will start automatically when deployed to Hugging Face Spaces."
echo "   For local testing, run: python app.py"