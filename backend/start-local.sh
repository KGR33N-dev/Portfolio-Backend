#!/bin/bash

echo "🚀 Starting Portfolio Backend Locally..."

# Load environment variables
export $(cat .env | grep -v '#' | awk '/=/ {print $1}')

# Stop any running containers
echo "🛑 Stopping existing containers..."
sudo docker compose down

# Build and start containers
echo "🔨 Building and starting containers..."
sudo docker compose up --build -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Check container status
echo "📊 Container Status:"
sudo docker compose ps

# Show logs
echo "📋 Application Logs:"
sudo docker compose logs web --tail=20

echo "✅ Local development server started!"
echo "🌐 API available at: http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo "🔍 Database: localhost:5432 (postgres/password)"

echo ""
echo "🔧 Useful commands:"
echo "  View logs: sudo docker compose logs web -f"
echo "  Stop: sudo docker compose down"
echo "  Restart: sudo docker compose restart"
echo "  Database shell: sudo docker compose exec db psql -U postgres -d portfolio"