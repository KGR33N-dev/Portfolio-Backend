#!/bin/bash

# Uruchamianie FastAPI z migracjami Alembic
echo "🐘 Czekam na bazę danych..."

# Wait for database to be ready
python -c "
import os
import time
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def wait_for_db():
    while True:
        try:
            DATABASE_URL = os.getenv('DATABASE_URL')
            if not DATABASE_URL:
                raise ValueError('DATABASE_URL not set')
            
            # Parse DATABASE_URL
            from urllib.parse import urlparse
            result = urlparse(DATABASE_URL)
            
            conn = psycopg2.connect(
                host=result.hostname,
                port=result.port,
                user=result.username,
                password=result.password,
                database=result.path[1:]  # Remove leading slash
            )
            conn.close()
            print('✅ Połączenie z bazą danych zostało nawiązane!')
            break
        except psycopg2.OperationalError:
            print('⏳ Czekam na bazę danych...')
            time.sleep(2)
        except Exception as e:
            print(f'❌ Błąd: {e}')
            time.sleep(2)

if __name__ == '__main__':
    wait_for_db()
"

echo "🔄 Sprawdzam stan migracji..."

# Check if any migration files exist
MIGRATION_FILES=$(find alembic/versions -name "*.py" -not -name "__init__.py" 2>/dev/null | wc -l)

if [ "$MIGRATION_FILES" -eq 0 ]; then
    echo "📝 Brak plików migracji - przygotowuję świeże środowisko..."
    
    # Clear alembic version table if it exists and reset alembic
    echo "🧹 Czyszczę historię migracji Alembic..."
    python -c "
import os
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

try:
    DATABASE_URL = os.getenv('DATABASE_URL')
    result = urlparse(DATABASE_URL)
    
    conn = psycopg2.connect(
        host=result.hostname,
        port=result.port,
        user=result.username,
        password=result.password,
        database=result.path[1:]
    )
    
    with conn.cursor() as cursor:
        # Drop alembic_version table if it exists
        cursor.execute('DROP TABLE IF EXISTS alembic_version CASCADE;')
        conn.commit()
        print('✅ Tabela alembic_version została usunięta!')
    
    conn.close()
except Exception as e:
    print(f'⚠️  Info: {e}')
"
    
    # Remove any existing alembic directories and reinitialize
    echo "🔄 Resetuję konfigurację Alembic..."
    rm -rf alembic/versions/*
    
    # Initialize alembic with current HEAD
    echo "📝 Inicjalizuję nową historię migracji..."
    alembic stamp head --purge 2>/dev/null || true
    
    echo "📝 Tworzę pierwszą migrację..."
    alembic revision --autogenerate -m "Initial schema"
    
    if [ $? -eq 0 ]; then
        echo "✅ Pierwsza migracja została utworzona!"
    else
        echo "❌ Błąd podczas tworzenia migracji!"
        exit 1
    fi
fi

echo "🔄 Uruchamiam migracje Alembic..."

# Run database migrations
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migracje zakończone pomyślnie!"
else
    echo "❌ Błąd podczas migracji!"
    exit 1
fi

echo "🚀 Uruchamiam FastAPI..."
echo "💡 Aby utworzyć administratora, wejdź do kontenera i uruchom:"
echo "   docker compose exec web python app/create_admin.py"

# Start the FastAPI application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
