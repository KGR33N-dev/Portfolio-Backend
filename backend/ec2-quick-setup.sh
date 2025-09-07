#!/bin/bash

# EC2 Quick Setup Script
# Run this after connecting to EC2 via SSH

echo "🚀 EC2 Quick Setup for Portfolio Backend"
echo "========================================"

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y git curl wget nano htop

# Clone repository
git clone https://github.com/KGR33N-dev/Portfolio-Backend.git
cd Portfolio-Backend/backend

# Make scripts executable
chmod +x secure-deploy.sh
chmod +x check-production-config.sh

echo "✅ Basic setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Run: ./secure-deploy.sh"
echo "2. After reboot, run: ./secure-deploy.sh again"
echo "3. Configure DNS and SSL"
