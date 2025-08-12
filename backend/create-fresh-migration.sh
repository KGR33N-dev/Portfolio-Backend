#!/bin/bash

echo "🔄 Tworzenie nowej, czystej migracji..."

# Check if we're in the backend directory
if [[ ! -f "alembic.ini" ]]; then
    echo "❌ Nie znaleziono alembic.ini - upewnij się, że jesteś w katalogu backend/"
    exit 1
fi

# Detect docker compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Nie znaleziono docker-compose ani docker compose"
    exit 1
fi

# Make sure containers are running
echo "🚀 Sprawdzanie czy kontenery działają..."
if ! $DOCKER_COMPOSE ps | grep -q "Up"; then
    echo "🔧 Uruchamianie kontenerów..."
    $DOCKER_COMPOSE up -d db
    sleep 10
fi

# Create fresh migration
echo "📝 Generowanie nowej migracji..."
$DOCKER_COMPOSE exec web alembic revision --autogenerate -m "Initial schema"

echo "✅ Nowa migracja została utworzona!"
echo "💡 Teraz możesz uruchomić migrację poleceniem:"
echo "   docker-compose exec web alembic upgrade head"
