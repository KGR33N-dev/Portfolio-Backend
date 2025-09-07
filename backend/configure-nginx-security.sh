#!/bin/bash

# Configure Nginx with security restrictions
# Run this script after secure-deploy.sh

echo "🔒 Configuring Nginx with security restrictions..."

# Get your current IP
YOUR_IP=$(curl -s ifconfig.me)
echo "🌐 Your IP detected as: $YOUR_IP"

# Create secure nginx config
sudo tee /etc/nginx/sites-available/portfolio-secure > /dev/null <<EOF
# Rate limiting zones
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=auth:10m rate=5r/s;

# Allowed origins map
map \$http_origin \$cors_origin {
    default "";
    "https://kgr33n.com" "https://kgr33n.com";
    "https://www.kgr33n.com" "https://www.kgr33n.com";
    "http://localhost:4321" "http://localhost:4321";
}

server {
    listen 80;
    server_name api.kgr33n.com;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Cloudflare real IP
    set_real_ip_from 173.245.48.0/20;
    set_real_ip_from 103.21.244.0/22;
    set_real_ip_from 103.22.200.0/22;
    set_real_ip_from 103.31.4.0/22;
    set_real_ip_from 141.101.64.0/18;
    set_real_ip_from 108.162.192.0/18;
    set_real_ip_from 190.93.240.0/20;
    set_real_ip_from 188.114.96.0/20;
    set_real_ip_from 197.234.240.0/22;
    set_real_ip_from 198.41.128.0/17;
    set_real_ip_from 162.158.0.0/15;
    set_real_ip_from 104.16.0.0/13;
    set_real_ip_from 104.24.0.0/14;
    set_real_ip_from 172.64.0.0/13;
    set_real_ip_from 131.0.72.0/22;
    real_ip_header CF-Connecting-IP;
    
    # Block direct IP access
    if (\$host != "api.kgr33n.com") {
        return 444;
    }
    
    # Health check (public)
    location /health {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # CORS test (public for debugging)
    location /cors-test {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # API endpoints with restrictions
    location /api/ {
        limit_req zone=api burst=50 nodelay;
        
        # Origin restrictions
        set \$allowed 0;
        if (\$cors_origin != "") {
            set \$allowed 1;
        }
        if (\$remote_addr = "$YOUR_IP") {
            set \$allowed 1;
        }
        if (\$allowed = 0) {
            return 403;
        }
        
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin \$cors_origin always;
        add_header Access-Control-Allow-Credentials "true" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
        
        if (\$request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin \$cors_origin;
            add_header Access-Control-Allow-Credentials "true";
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain; charset=utf-8';
            add_header Content-Length 0;
            return 204;
        }
    }
    
    # Block all other requests
    location / {
        return 444;
    }
}
EOF

# Enable the new config
sudo rm -f /etc/nginx/sites-enabled/portfolio
sudo ln -sf /etc/nginx/sites-available/portfolio-secure /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload nginx
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Nginx configured with security restrictions"
echo "📝 Your IP ($YOUR_IP) has been whitelisted for API access"
echo ""
echo "📋 Next: Configure Cloudflare DNS to point api.kgr33n.com to this server"
