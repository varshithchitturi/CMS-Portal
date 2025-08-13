#!/bin/bash

# Deployment script for Complaint Management System

echo "🚀 Starting deployment of Complaint Management System..."

# Create data directory if it doesn't exist
mkdir -p data

# Copy environment variables
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please create it with your environment variables."
    exit 1
fi

# Build and start the application
echo "📦 Building Docker image..."
docker-compose build

echo "🔄 Starting services..."
docker-compose up -d

echo "⏳ Waiting for application to start..."
sleep 10

# Check if application is running
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Application is running successfully!"
    echo "🌐 Access your application at: http://localhost:5000"
    echo "📊 Health check: http://localhost:5000/health"
else
    echo "❌ Application failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo "📋 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop app: docker-compose down"
echo "  Restart: docker-compose restart"