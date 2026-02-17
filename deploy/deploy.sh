#!/bin/bash

# Deployment Script for ExamForge
# This script deploys or updates the ExamForge application
# Run with: bash deploy.sh

set -e

echo "========================================="
echo "ExamForge Deployment Script"
echo "========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.production to .env and configure it."
    exit 1
fi

# Check if GEMINI_API_KEY is set
if ! grep -q "GEMINI_API_KEY=your_gemini_api_key_here" .env; then
    echo "✓ GEMINI_API_KEY appears to be configured"
else
    echo "Warning: GEMINI_API_KEY might not be configured in .env"
    echo "Make sure to update it before deploying"
fi

# Pull latest changes (if using git)
echo "[1/5] Checking for updates..."
if [ -d .git ]; then
    echo "Pulling latest changes from git..."
    git pull
else
    echo "Not a git repository, skipping pull"
fi

# Stop existing containers
echo "[2/5] Stopping existing containers..."
if docker-compose -f docker-compose.prod.yml ps -q 2>/dev/null; then
    docker-compose -f docker-compose.prod.yml down
fi

# Build images
echo "[3/5] Building Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Start containers
echo "[4/5] Starting containers..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "[5/5] Waiting for services to start..."
sleep 10

# Health check
echo ""
echo "Performing health checks..."
if curl -f http://localhost:80/health > /dev/null 2>&1; then
    echo "✓ Frontend health check passed"
else
    echo "✗ Frontend health check failed"
fi

if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✓ Backend health check passed"
else
    echo "✗ Backend health check failed (might be internal only)"
fi

# Show container status
echo ""
echo "Container status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Your application should now be running at:"
echo "http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'YOUR_EC2_IP')"
echo ""
echo "Useful commands:"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  Stop app: docker-compose -f docker-compose.prod.yml down"
echo "  Restart: docker-compose -f docker-compose.prod.yml restart"
echo ""
