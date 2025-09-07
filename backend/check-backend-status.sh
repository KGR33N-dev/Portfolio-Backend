#!/bin/bash

echo "🔍 Sprawdzanie statusu backendu na EC2..."
echo "========================================"

echo ""
echo "1. 🐳 Status Docker:"
docker --version
sudo systemctl is-active docker

echo ""
echo "2. 📦 Uruchomione kontenery:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "3. 🌐 Sprawdzanie portów:"
echo "Port 8080 (backend):"
sudo netstat -tlnp | grep :8080 || echo "❌ Port 8080 nie jest otwarty"

echo "Port 80 (nginx):"
sudo netstat -tlnp | grep :80 || echo "❌ Port 80 nie jest otwarty"

echo "Port 443 (nginx SSL):"
sudo netstat -tlnp | grep :443 || echo "❌ Port 443 nie jest otwarty"

echo ""
echo "4. 🔥 Status firewall:"
sudo ufw status

echo ""
echo "5. 🌍 Test lokalnego połączenia:"
echo "Backend health check:"
curl -s http://localhost:8080/health || echo "❌ Backend nie odpowiada lokalnie"

echo ""
echo "Test zewnętrznego połączenia:"
curl -s http://13.48.70.51:8080/health || echo "❌ Backend nie odpowiada zewnętrznie"

echo ""
echo "6. 📋 Logi backendu (ostatnie 10 linii):"
docker logs --tail 10 $(docker ps -q --filter "name=app") 2>/dev/null || echo "❌ Nie można pobrać logów"

echo ""
echo "7. 📁 Sprawdzanie plików konfiguracyjnych:"
if [ -f "/home/ubuntu/Portfolio-Backend/backend/.env.production" ]; then
    echo "✅ .env.production istnieje"
    echo "ALLOWED_ORIGINS:"
    grep ALLOWED_ORIGINS /home/ubuntu/Portfolio-Backend/backend/.env.production || echo "❌ Brak ALLOWED_ORIGINS"
else
    echo "❌ Brak pliku .env.production"
fi

echo ""
echo "8. 🔧 Nginx status (jeśli zainstalowany):"
if command -v nginx &> /dev/null; then
    sudo systemctl is-active nginx
    sudo nginx -t
else
    echo "❌ Nginx nie jest zainstalowany"
fi

echo ""
echo "========================================"
echo "🎯 Diagnoza zakończona!"
