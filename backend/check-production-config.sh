#!/bin/bash

echo "🔍 SPRAWDZANIE KONFIGURACJI CORS I COOKIES"
echo "============================================"

echo ""
echo "1. 📋 Sprawdzanie zmiennych środowiskowych:"
echo "-------------------------------------------"
if [ -f ".env.production" ]; then
    echo "✅ .env.production istnieje"
    echo ""
    echo "🌐 CORS Configuration:"
    grep "ALLOWED_ORIGINS" .env.production || echo "❌ Brak ALLOWED_ORIGINS"
    echo ""
    echo "🌍 Frontend URLs:"
    grep -E "(FRONTEND_URL|PRODUCTION_FRONTEND|BACKEND_URL)" .env.production
    echo ""
    echo "🔒 Environment:"
    grep "ENVIRONMENT" .env.production
else
    echo "❌ Brak pliku .env.production"
fi

echo ""
echo "2. 🐳 Status Docker:"
echo "-------------------"
if command -v docker &> /dev/null; then
    echo "✅ Docker jest dostępny"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -10
else
    echo "❌ Docker nie jest dostępny"
fi

echo ""
echo "3. 🌐 Test połączenia lokalnego:"
echo "-------------------------------"
echo "Backend health (port 8080):"
curl -s -m 5 http://localhost:8080/health | jq . 2>/dev/null || echo "❌ Backend nie odpowiada na localhost:8080"

echo ""
echo "CORS test (port 8080):"
curl -s -m 5 http://localhost:8080/cors-test | jq . 2>/dev/null || echo "❌ CORS test nie działa"

echo ""
echo "4. 🌍 Test połączenia zewnętrznego:"
echo "----------------------------------"
PUBLIC_IP=$(curl -s -m 5 ifconfig.me 2>/dev/null || echo "unknown")
echo "🔧 Publiczny IP: $PUBLIC_IP"

if [ "$PUBLIC_IP" != "unknown" ]; then
    echo "Backend health (zewnętrzny IP:8080):"
    curl -s -m 5 http://$PUBLIC_IP:8080/health | jq . 2>/dev/null || echo "❌ Backend nie odpowiada zewnętrznie"
fi

echo ""
echo "5. 🔥 Status firewall:"
echo "---------------------"
if command -v ufw &> /dev/null; then
    sudo ufw status | head -20
else
    echo "❌ UFW nie jest zainstalowany"
fi

echo ""
echo "6. 📱 Porty w użyciu:"
echo "--------------------"
echo "Port 8080 (backend):"
sudo netstat -tlnp | grep :8080 || echo "❌ Port 8080 nie jest otwarty"

echo ""
echo "Port 80 (nginx):"
sudo netstat -tlnp | grep :80 || echo "❌ Port 80 nie jest otwarty"

echo ""
echo "Port 443 (nginx SSL):"
sudo netstat -tlnp | grep :443 || echo "❌ Port 443 nie jest otwarty"

echo ""
echo "7. 📄 Logi aplikacji:"
echo "--------------------"
echo "Ostatnie 5 linii logów:"
docker logs --tail 5 $(docker ps -q --filter "name=app") 2>/dev/null || echo "❌ Nie można pobrać logów aplikacji"

echo ""
echo "8. 🔧 Nginx status (jeśli zainstalowany):"
echo "----------------------------------------"
if command -v nginx &> /dev/null; then
    echo "Status nginx:"
    sudo systemctl is-active nginx
    echo ""
    echo "Test konfiguracji nginx:"
    sudo nginx -t
else
    echo "❌ Nginx nie jest zainstalowany"
fi

echo ""
echo "============================================"
echo "🎯 DIAGNOZA ZAKOŃCZONA!"
echo ""
echo "📝 NASTĘPNE KROKI:"
echo "1. Jeśli backend nie odpowiada - sprawdź docker-compose"
echo "2. Jeśli CORS błędy - sprawdź domenę w Cloudflare"
echo "3. Jeśli cookies nie działają - sprawdź HTTPS"
echo "4. Status 522 = brak połączenia backend ↔ Cloudflare"
