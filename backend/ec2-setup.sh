#!/bin/bash

# EC2 Instance Setup Script for Portfolio Backend
# Run this script on a fresh EC2 Amazon Linux 2 instance

set -e  # Exit on error

echo "🚀 Setting up EC2 instance for Portfolio Backend..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Update system
echo "📦 Updating system packages..."
sudo yum update -y

# Install Docker
echo "🐳 Installing Docker..."
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
echo "📋 Installing Git..."
sudo yum install git -y

# Install Nginx
echo "🌐 Installing Nginx..."
sudo amazon-linux-extras install nginx1 -y

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /opt/portfolio-backend
sudo chown ec2-user:ec2-user /opt/portfolio-backend

# Create systemd service for the application
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/portfolio-backend.service > /dev/null <<EOF
[Unit]
Description=Portfolio Backend API
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/portfolio-backend
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0
User=ec2-user

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/conf.d/portfolio-backend.conf > /dev/null <<EOF
server {
    listen 80;
    server_name api.yourdomain.com;  # Change this to your domain

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # CORS headers for API
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
        
        # Handle preflight requests
        if (\$request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }

    # Health check endpoint
    location /api/health {
        proxy_pass http://localhost:8000/api/health;
        access_log off;
    }
}
EOF

# Enable and start services
echo "🔄 Enabling services..."
sudo systemctl enable docker
sudo systemctl enable nginx
sudo systemctl enable portfolio-backend

# Start Nginx
sudo systemctl start nginx

echo -e "${GREEN}✅ EC2 setup completed!${NC}"
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Clone your repository to /opt/portfolio-backend"
echo "2. Create .env file with your configuration"
echo "3. Run: sudo systemctl start portfolio-backend"
echo "4. Update Nginx config with your actual domain"
echo "5. Set up SSL certificate (Let's Encrypt recommended)"

echo -e "${GREEN}🔧 Example commands:${NC}"
echo "cd /opt/portfolio-backend"
echo "git clone YOUR_REPO_URL ."
echo "cp .env.example .env"
echo "# Edit .env with your settings"
echo "sudo systemctl start portfolio-backend"
