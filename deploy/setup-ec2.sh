#!/bin/bash

# EC2 Setup Script for ExamForge
# This script prepares a fresh EC2 instance (Ubuntu) for running the application
# Run with: sudo bash setup-ec2.sh

set -e

echo "========================================="
echo "ExamForge EC2 Setup Script"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Update system packages
echo "[1/8] Updating system packages..."
apt-get update
apt-get upgrade -y

# Install required packages
echo "[2/8] Installing required packages..."
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    htop \
    vim \
    unattended-upgrades

# Install Docker
echo "[3/8] Installing Docker..."
if ! command -v docker &> /dev/null; then
    # Add Docker's official GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Set up the repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker Engine
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    echo "Docker installed successfully"
else
    echo "Docker already installed"
fi

# Install Docker Compose standalone (v2)
echo "[4/8] Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION="v2.24.5"
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installed successfully"
else
    echo "Docker Compose already installed"
fi

# Enable Docker service
echo "[5/8] Enabling Docker service..."
systemctl enable docker
systemctl start docker

# Add ubuntu user to docker group
echo "[6/8] Adding ubuntu user to docker group..."
if id "ubuntu" &>/dev/null; then
    usermod -aG docker ubuntu
    echo "User 'ubuntu' added to docker group"
fi

# Setup swap file (recommended for t3.micro - 2GB)
echo "[7/8] Setting up swap file..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    
    # Make swap permanent
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
    
    # Optimize swap usage
    sysctl vm.swappiness=10
    echo 'vm.swappiness=10' | tee -a /etc/sysctl.conf
    
    echo "Swap file created (2GB)"
else
    echo "Swap file already exists"
fi

# Configure firewall (UFW)
echo "[8/8] Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS (for future use)
ufw reload

echo ""
echo "========================================="
echo "EC2 Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Log out and log back in for docker group changes to take effect"
echo "2. Clone your ExamForge repository"
echo "3. Navigate to the project directory"
echo "4. Copy .env.production to .env and add your GEMINI_API_KEY"
echo "5. Run: docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "Verification:"
echo "- Check Docker: docker --version"
echo "- Check Docker Compose: docker-compose --version"
echo "- Check running containers: docker ps"
echo ""
