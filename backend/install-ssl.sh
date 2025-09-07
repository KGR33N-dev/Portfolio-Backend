#!/bin/bash

# Install SSL certificates with Let's Encrypt
# Run this after nginx is configured and DNS is pointing to server

echo "🔒 Installing SSL certificates with Let's Encrypt..."

# Install certbot
echo "📦 Installing certbot..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Check if DNS is configured properly
echo "🌐 Checking DNS configuration..."
EXPECTED_IP="13.48.70.51"
ACTUAL_IP=$(dig +short api.kgr33n.com @8.8.8.8)

if [ "$ACTUAL_IP" != "$EXPECTED_IP" ]; then
    echo "❌ DNS not configured properly!"
    echo "Expected: $EXPECTED_IP"
    echo "Actual: $ACTUAL_IP"
    echo ""
    echo "Please configure DNS first:"
    echo "1. Go to Cloudflare dashboard"
    echo "2. Add A record: api.kgr33n.com → $EXPECTED_IP"
    echo "3. Enable proxy (orange cloud)"
    echo "4. Wait 5-10 minutes for propagation"
    exit 1
fi

echo "✅ DNS configured correctly: $ACTUAL_IP"

# Test if nginx is responding
echo "🔍 Testing nginx configuration..."
if curl -f http://api.kgr33n.com/health > /dev/null 2>&1; then
    echo "✅ Nginx is responding correctly"
else
    echo "❌ Nginx is not responding. Check configuration:"
    sudo nginx -t
    sudo systemctl status nginx
    exit 1
fi

# Install SSL certificate
echo "🔐 Installing SSL certificate..."
sudo certbot --nginx -d api.kgr33n.com --non-interactive --agree-tos --email admin@kgr33n.com

if [ $? -eq 0 ]; then
    echo "✅ SSL certificate installed successfully!"
    
    # Test HTTPS
    if curl -f https://api.kgr33n.com/health > /dev/null 2>&1; then
        echo "✅ HTTPS is working correctly"
    else
        echo "⚠️  HTTPS test failed, but certificate was installed"
    fi
    
    # Setup auto-renewal
    sudo systemctl enable certbot.timer
    sudo systemctl start certbot.timer
    echo "✅ Auto-renewal configured"
    
    echo ""
    echo "🎉 SSL setup completed!"
    echo "📋 Test your API:"
    echo "• Health: https://api.kgr33n.com/health"
    echo "• CORS: curl -H 'Origin: https://kgr33n.com' https://api.kgr33n.com/cors-test"
    
else
    echo "❌ SSL certificate installation failed"
    echo "Check the logs above for details"
    exit 1
fi
