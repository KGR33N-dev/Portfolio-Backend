#!/bin/bash

# EC2 Quick Setup echo "📋 Available scripts:"
echo "• ./nuclear-reset.sh - 💥 COMPLETE RESET (keeps .env.production)"
echo "• ./clean-deploy.sh - Complete fresh deployment (regenerates credentials)"
echo "• ./secure-deploy.sh - Full deployment (if Docker not installed)"
echo "• ./deploy-app-only.sh - Deploy app (if Docker already installed)"
echo "• ./fix-database.sh - Fix database user issues"
echo "• ./configure-nginx-security.sh - Configure nginx with security"
echo "• ./install-ssl.sh - Install SSL certificates"
echo "• ./test-deployment.sh - Test the deployment"
echo "• ./check-production-config.sh - Diagnostic tool"
echo ""
echo "🚨 FOR COMPLETE RESET (keeps your .env.production):"
echo "1. Run: ./nuclear-reset.sh"
echo "2. Continue with nginx and SSL setup"his after connecting to EC2 via SSH

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
chmod +x configure-nginx-security.sh
chmod +x deploy-app-only.sh
chmod +x install-ssl.sh
chmod +x test-deployment.sh
chmod +x fix-database.sh
chmod +x clean-deploy.sh
chmod +x nuclear-reset.sh

echo "✅ Basic setup completed!"
echo ""
echo "📋 Available scripts:"
echo "• ./nuclear-reset.sh - 💥 COMPLETE RESET (removes everything!)"
echo "• ./clean-deploy.sh - Complete fresh deployment"
echo "• ./secure-deploy.sh - Full deployment (if Docker not installed)"
echo "• ./deploy-app-only.sh - Deploy app (if Docker already installed)"
echo "• ./fix-database.sh - Fix database user issues"
echo "• ./configure-nginx-security.sh - Configure nginx with security"
echo "• ./install-ssl.sh - Install SSL certificates"
echo "• ./test-deployment.sh - Test the deployment"
echo "• ./check-production-config.sh - Diagnostic tool"
echo ""
echo "� FOR COMPLETE RESET (when nothing works):"
echo "1. Run: ./nuclear-reset.sh"
echo "2. Continue with nginx and SSL setup"
echo ""
echo "📋 For normal fresh deployment:"
echo "1. Run: ./clean-deploy.sh"
echo "2. Run: ./configure-nginx-security.sh"
echo "3. Configure DNS: api.kgr33n.com → $(curl -s ifconfig.me)"
echo "4. Run: ./install-ssl.sh"
