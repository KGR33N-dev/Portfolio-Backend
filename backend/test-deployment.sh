#!/bin/bash

# Quick test of the deployed application

echo "🧪 Testing Portfolio Backend Deployment"
echo "======================================"

# Check Docker services
echo "🐳 Docker Services:"
docker-compose -f /home/ubuntu/Portfolio-Backend/backend/docker-compose.prod.yml ps

echo ""
echo "🏥 Health Checks:"

# Test local health
echo -n "• Local health (8080): "
if curl -s -f http://localhost:8080/health > /dev/null; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Test CORS endpoint
echo -n "• CORS test: "
if curl -s -f http://localhost:8080/cors-test > /dev/null; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Test through nginx (if configured)
echo -n "• Nginx proxy (80): "
if curl -s -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ FAILED or not configured"
fi

# Test external access
PUBLIC_IP=$(curl -s ifconfig.me)
echo -n "• External health: "
if curl -s -f http://$PUBLIC_IP:8080/health > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ FAILED (firewall may be blocking)"
fi

# Test domain (if DNS configured)
echo -n "• Domain health: "
if curl -s -f http://api.kgr33n.com/health > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ FAILED (DNS not configured or SSL needed)"
fi

# Test HTTPS (if SSL configured)
echo -n "• HTTPS health: "
if curl -s -f https://api.kgr33n.com/health > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ FAILED (SSL not configured)"
fi

echo ""
echo "🌐 Network Info:"
echo "• Public IP: $PUBLIC_IP"
echo "• DNS check: $(dig +short api.kgr33n.com @8.8.8.8)"

echo ""
echo "📊 Recent Logs (last 10 lines):"
docker-compose -f /home/ubuntu/Portfolio-Backend/backend/docker-compose.prod.yml logs --tail=10 app

echo ""
echo "📋 Quick Commands:"
echo "• View logs: docker-compose -f /home/ubuntu/Portfolio-Backend/backend/docker-compose.prod.yml logs -f app"
echo "• Restart: docker-compose -f /home/ubuntu/Portfolio-Backend/backend/docker-compose.prod.yml restart"
echo "• Stop: docker-compose -f /home/ubuntu/Portfolio-Backend/backend/docker-compose.prod.yml down"
