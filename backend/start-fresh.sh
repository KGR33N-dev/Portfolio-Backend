#!/bin/bash

echo "🧹 FRESH START - Czyszczenie wszystkich danych..."

# Detect docker compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Nie znaleziono docker-compose ani docker compose"
    exit 1
fi

echo "📦 Używam: $DOCKER_COMPOSE"

# Stop and remove containers with volumes
echo "🛑 Zatrzymywanie kontenerów..."
$DOCKER_COMPOSE down -v --remove-orphans

# Remove all stopped containers
echo "🗑️  Usuwanie kontenerów..."
docker container prune -f

# Remove all unused volumes
echo "💾 Usuwanie woluminów..."
docker volume prune -f

# Remove portfolio-specific volumes if they exist
docker volume rm backend_postgres_data 2>/dev/null || true
docker volume rm portfolio-backend_postgres_data 2>/dev/null || true
docker volume ls | grep postgres | awk '{print $2}' | xargs -r docker volume rm 2>/dev/null || true

# Remove all unused networks  
echo "🌐 Usuwanie sieci..."
docker network prune -f

# Remove unused images
echo "🖼️  Usuwanie nieużywanych obrazów..."
docker image prune -f

# Remove alembic cache
echo "🗂️  Usuwanie cache Alembic..."
rm -rf alembic/versions/__pycache__
rm -rf app/__pycache__
rm -rf app/routers/__pycache__

echo "✨ Wszystko wyczyszczone!"
echo "🚀 Uruchamianie z kompletnie czystą bazą danych..."

# Start with clean slate
$DOCKER_COMPOSE up --build
