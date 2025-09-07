#!/bin/bash

# Secure Production Deployment Script
# This script sets up a secure production environment with PostgreSQL in Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Secure Production Deployment Script${NC}"
echo "========================================"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ This script should not be run as root for security reasons${NC}"
   echo "Run as ubuntu user: sudo su - ubuntu"
   exit 1
fi

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to generate random secret key
generate_secret_key() {
    openssl rand -hex 32
}

# System update and security hardening
system_security_setup() {
    echo -e "${YELLOW}🔒 Setting up system security...${NC}"
    
    # Update system
    sudo apt update
    sudo apt upgrade -y
    
    # Install essential security packages
    sudo apt install -y \
        ufw \
        fail2ban \
        unattended-upgrades \
        apt-listchanges \
        curl \
        wget \
        git \
        htop \
        nano \
        jq
    
    # Configure UFW firewall
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 8080/tcp  # Backend port
    sudo ufw --force enable
    
    # Configure fail2ban
    sudo systemctl enable fail2ban
    sudo systemctl start fail2ban
    
    # Configure automatic security updates
    echo 'Unattended-Upgrade::Automatic-Reboot "false";' | sudo tee -a /etc/apt/apt.conf.d/50unattended-upgrades
    
    echo -e "${GREEN}✅ System security configured${NC}"
}

# Install Docker and Docker Compose
install_docker() {
    echo -e "${YELLOW}🐳 Installing Docker...${NC}"
    
    # Remove old versions
    sudo apt remove -y docker docker-engine docker.io containerd runc || true
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    # Install Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Start Docker
    sudo systemctl enable docker
    sudo systemctl start docker
    
    echo -e "${GREEN}✅ Docker installed${NC}"
    echo -e "${YELLOW}⚠️  You need to log out and back in for Docker group changes to take effect${NC}"
}

# Setup application
setup_application() {
    echo -e "${YELLOW}📁 Setting up application...${NC}"
    
    # Create application directory
    APP_DIR="/home/ubuntu/Portfolio-Backend"
    if [ ! -d "$APP_DIR" ]; then
        echo "Cloning repository..."
        git clone https://github.com/KGR33N-dev/Portfolio-Backend.git $APP_DIR
    fi
    
    cd $APP_DIR/backend
    
    # Generate secure passwords and keys
    DB_PASSWORD=$(generate_password)
    SECRET_KEY=$(generate_secret_key)
    ADMIN_PASSWORD=$(generate_password)
    
    echo -e "${BLUE}📝 Generated secure credentials:${NC}"
    echo "Database Password: $DB_PASSWORD"
    echo "Secret Key: $SECRET_KEY"
    echo "Admin Password: $ADMIN_PASSWORD"
    echo ""
    echo -e "${YELLOW}⚠️  SAVE THESE CREDENTIALS SECURELY!${NC}"
    echo ""
    
    # Create production environment file
    cp .env.production .env.production.backup 2>/dev/null || true
    
    # Update .env.production with generated values
    sed -i "s/CHANGE_DB_PASSWORD_HERE/$DB_PASSWORD/g" .env.production
    sed -i "s/CHANGE_THIS_TO_RANDOM_64_CHAR_HEX_STRING_GENERATE_NEW/$SECRET_KEY/g" .env.production
    sed -i "s/CHANGE_TO_VERY_STRONG_PASSWORD_MIN_16_CHARS/$ADMIN_PASSWORD/g" .env.production
    
    # Set secure file permissions
    chmod 600 .env.production
    
    echo -e "${GREEN}✅ Application configured${NC}"
}

# Deploy application with Docker
deploy_application() {
    echo -e "${YELLOW}🚀 Deploying application...${NC}"
    
    cd /home/ubuntu/Portfolio-Backend/backend
    
    # Pull latest changes
    git pull origin main 2>/dev/null || git pull origin dev
    
    # Build and start services
    docker-compose -f docker-compose.prod.yml down || true
    docker-compose -f docker-compose.prod.yml build
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for database to be ready
    echo "Waiting for database to be ready..."
    sleep 30
    
    # Run database migrations
    echo "Running database migrations..."
    docker-compose -f docker-compose.prod.yml exec -T app alembic upgrade head
    
    # Create admin user
    echo "Creating admin user..."
    docker-compose -f docker-compose.prod.yml exec -T app python app/create_admin.py
    
    echo -e "${GREEN}✅ Application deployed${NC}"
}

# Setup SSL with Let's Encrypt
setup_ssl() {
    echo -e "${YELLOW}🔒 Setting up SSL certificates...${NC}"
    
    # Install Certbot
    sudo apt install -y certbot python3-certbot-nginx
    
    # Install Nginx
    sudo apt install -y nginx
    
    # Create basic Nginx config
    sudo tee /etc/nginx/sites-available/portfolio > /dev/null <<EOF
server {
    listen 80;
    server_name api.kgr33n.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/portfolio /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test Nginx config
    sudo nginx -t
    sudo systemctl restart nginx
    
    echo -e "${YELLOW}⚠️  Configure DNS first, then run:${NC}"
    echo "sudo certbot --nginx -d api.kgr33n.com"
    
    echo -e "${GREEN}✅ Nginx configured${NC}"
}

# Health check
health_check() {
    echo -e "${YELLOW}🏥 Running health checks...${NC}"
    
    # Check Docker services
    docker-compose -f /home/ubuntu/Portfolio-Backend/backend/docker-compose.prod.yml ps
    
    # Check application health
    sleep 10
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Application is healthy${NC}"
    else
        echo -e "${RED}❌ Application health check failed${NC}"
        docker-compose -f /home/ubuntu/Portfolio-Backend/backend/docker-compose.prod.yml logs app
    fi
    
    # Check database
    if docker-compose -f /home/ubuntu/Portfolio-Backend/backend/docker-compose.prod.yml exec -T db pg_isready > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Database is healthy${NC}"
    else
        echo -e "${RED}❌ Database health check failed${NC}"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}Starting secure production deployment...${NC}"
    echo ""
    
    # Check if first run
    if [ ! -f "/home/ubuntu/.portfolio_deployed" ]; then
        system_security_setup
        install_docker
        echo -e "${YELLOW}⚠️  Please log out and back in, then run this script again${NC}"
        touch /home/ubuntu/.portfolio_deployed_step1
        exit 0
    fi
    
    setup_application
    deploy_application
    setup_ssl
    health_check
    
    echo ""
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 Next steps:${NC}"
    echo "1. Configure DNS: api.kgr33n.com → $(curl -s ifconfig.me)"
    echo "2. Setup SSL: sudo certbot --nginx -d api.kgr33n.com"
    echo "3. Test API: https://api.kgr33n.com/health"
    echo ""
    echo -e "${BLUE}📱 Useful commands:${NC}"
    echo "• Check logs: docker-compose -f /home/ubuntu/Portfolio-Backend/backend/docker-compose.prod.yml logs -f app"
    echo "• Restart app: docker-compose -f /home/ubuntu/Portfolio-Backend/backend/docker-compose.prod.yml restart"
    echo "• View status: docker-compose -f /home/ubuntu/Portfolio-Backend/backend/docker-compose.prod.yml ps"
    
    touch /home/ubuntu/.portfolio_deployed
}

# Run main function
main "$@"
