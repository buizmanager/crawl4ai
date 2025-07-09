#!/bin/bash

# Setup script for Crawl4AI Remote API Client

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit https://docs.docker.com/compose/install/ for installation instructions."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit the .env file to configure your environment variables."
fi

# Pull the Crawl4AI Docker image
echo "Pulling the Crawl4AI Docker image..."
docker pull unclecode/crawl4ai:latest

# Build and start the containers
echo "Building and starting the containers..."
docker-compose up -d

# Check if the containers are running
echo "Checking if the containers are running..."
if docker-compose ps | grep -q "crawl4ai-server"; then
    echo "✅ Crawl4AI server is running."
else
    echo "❌ Crawl4AI server failed to start. Please check the logs with 'docker-compose logs crawl4ai-server'."
fi

if docker-compose ps | grep -q "crawl4ai-client"; then
    echo "✅ Crawl4AI client is running."
else
    echo "❌ Crawl4AI client failed to start. Please check the logs with 'docker-compose logs crawl4ai-client'."
fi

echo ""
echo "Setup complete! You can access the Crawl4AI Remote API Client at:"
echo "http://localhost:7860"
echo ""
echo "To stop the containers, run:"
echo "docker-compose down"
echo ""
echo "To view the logs, run:"
echo "docker-compose logs -f"