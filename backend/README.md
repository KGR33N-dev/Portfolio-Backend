# Portfolio Backend

## 🚀 FastAPI Backend with Security System

Backend dla portfolio KGR33N z pełnym systemem bezpieczeństwa, autoryzacją JWT, API keys i rate limiting.

## 📋 Wymagania

- Python 3.8+
- PostgreSQL 13+
- Docker & Docker Compose
- Redis (opcjonalne, dla cache)

## 🔧 Instalacja i Setup

### 1. Klonowanie i instalacja zależności
```bash
git clone <repo-url>
cd Portfolio-Backend/backend
pip install -r requirements.txt
```

### 2. Konfiguracja bazy danych
```bash
# Utwórz bazę danych PostgreSQL
createdb portfolio_backend

# Ustaw zmienne środowiskowe
export DATABASE_URL="postgresql://username:password@localhost:5432/portfolio_backend"
export SECRET_KEY="your-super-secret-key-32-characters-long"
```

### 3. Migracje bazy danych
```bash
# Uruchom migracje
alembic upgrade head
```

### 4. **WAŻNE: Utworzenie pierwszego administratora**

Po skonfigurowaniu bazy danych **MUSISZ** utworzyć pierwszego użytkownika administratora:

```bash
# Interaktywne tworzenie admina
python app/create_admin.py

# Lub z parametrami
python app/create_admin.py --auto --username admin --email admin@kgr33n.com --password your-secure-password
```

**Przykład sesji interaktywnej:**
```
Creating first admin user...
Enter admin username: kgr33n
Enter admin email: admin@kgr33n.com
Enter admin password: [hasło-bezpieczne]
Enter full name (optional): KGR33N Admin

✅ Admin user created successfully!
Username: kgr33n
Email: admin@kgr33n.com
User ID: 1

You can now login to the admin panel with these credentials.
```

### 5. Uruchomienie aplikacji
```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production (Docker)
docker-compose -f docker-compose.prod.yml up -d
```

## 🔐 System Bezpieczeństwa

### Autoryzacja
- **JWT Tokens**: Dla użytkowników webowych (30 min ważności)
- **API Keys**: Dla aplikacji i integracji (customowy czas ważności)
- **Role-based**: System modularnych ról (user, admin, moderator) i rang (newbie, regular, trusted, star, legend, vip)
- **Permission-based**: Granularne uprawnienia per funkcjonalność

### Endpointy autoryzacji
```bash
POST /api/auth/register    # Rejestracja użytkownika
POST /api/auth/login       # Logowanie (zwraca JWT)
GET  /api/auth/me          # Info o aktualnym użytkowniku
POST /api/auth/api-keys    # Tworzenie API key (admin only)
GET  /api/auth/api-keys    # Lista API keys (admin only)
```

### Rate Limiting
- **Rejestracja**: 5 prób/godzina per IP
- **Logowanie**: 10 prób/15min per IP
- **Admin operacje**: 1000 prób/godzina
- **API operations**: 100 prób/godzina

## 📝 API Endpoints

### Publiczne (bez autoryzacji)
```bash
GET /api/blog/                    # Lista opublikowanych postów
GET /api/blog/{slug}              # Pojedynczy post
GET /api/blog/categories/list     # Lista kategorii
GET /api/blog/tags/list          # Lista tagów
GET /api/health                  # Health check
```

### Admin (wymaga JWT + rola Admin)
```bash
POST   /api/blog/           # Nowy post
PUT    /api/blog/{id}       # Edycja postu
DELETE /api/blog/{id}       # Usunięcie postu
PUT    /api/blog/{id}/publish  # Publikacja postu
```

## 🔑 Autoryzacja w praktyce

### JWT Token (dla interfejsu webowego)
```bash
# 1. Zaloguj się
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@kgr33n.com&password=your-password"

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {...}
}

# 2. Użyj token w nagłówkach
curl -X POST "http://localhost:8000/api/blog/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Post","slug":"test-post","content":"Content..."}'
```

### API Key (dla aplikacji)
```bash
# 1. Utwórz API key (jako admin)
curl -X POST "http://localhost:8000/api/auth/api-keys" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Frontend App","permissions":["read","write"],"expires_days":90}'

# 2. Użyj API key
curl -X GET "http://localhost:8000/api/blog/" \
  -H "X-API-Key: your-api-key-here"
```

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
# Ustaw zmienne środowiskowe w .env.production
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
ENVIRONMENT=production
DEBUG=False

# Deploy
docker-compose -f docker-compose.prod.yml up -d --build
```

## 🔧 Zmienne Środowiskowe

### Wymagane
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=your-super-secret-key-change-in-production
```

### Opcjonalne
```bash
# App settings
ENVIRONMENT=development          # development/production
DEBUG=True                      # True/False
FRONTEND_URL=http://localhost:4321
PRODUCTION_FRONTEND=https://kgr33n.com

# JWT settings
ACCESS_TOKEN_EXPIRE_MINUTES=30  # Czas ważności tokena w minutach
ALGORITHM=HS256                 # Algorytm szyfrowania JWT

# Database
POSTGRES_USER=fastapi_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=portfolio_backend
```

## 📊 Migracje

```bash
# Nowa migracja
alembic revision --autogenerate -m "Add new table"

# Zastosuj migracje
alembic upgrade head

# Cofnij migrację
alembic downgrade -1

# Historia migracji
alembic history
```

## 🛠️ Development

### Uruchomienie w trybie development
```bash
# Z auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Dokumentacja API dostępna na:
http://localhost:8000/api/docs      # Swagger UI
http://localhost:8000/api/redoc     # ReDoc
```

### Testowanie
```bash
# Uruchom testy
pytest

# Z coverage
pytest --cov=app

# Health check
curl http://localhost:8000/api/health
```

## 🚨 Troubleshooting

### Brak administratora
```bash
# Sprawdź czy istnieje admin
python -c "
from app.database import SessionLocal
from app.models import User
db = SessionLocal()
admin = db.query(User).filter(User.role = "Admin").first()
print(f'Admin user: {admin.username if admin else \"Not found\"}')
"

# Utwórz administratora
python app/create_admin.py
```

### Problemy z bazą danych
```bash
# Reset migracji (UWAGA: usuwa dane!)
alembic downgrade base
alembic upgrade head

# Sprawdź połączenie
python -c "
from app.database import engine
try:
    engine.connect()
    print('✅ Database connection OK')
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

### Problemy z kontenerami
```bash
# Sprawdź logi
docker-compose logs web

# Restart kontenerów
docker-compose restart

# Pełny rebuild
docker-compose down
docker-compose up -d --build
```

## 📝 Logs i Monitoring

```bash
# Logi aplikacji
docker-compose logs -f web

# Logi bazy danych
docker-compose logs -f db

# Health check
curl http://localhost:8000/api/health
```

## 🔒 Security Best Practices

1. **Zawsze zmień SECRET_KEY w produkcji**
2. **Używaj HTTPS w produkcji**
3. **Regularnie aktualizuj zależności**
4. **Monitoruj rate limiting**
5. **Regularnie sprawdzaj logi**
6. **Używaj silnych haseł dla adminów**
7. **Rotuj API keys regularnie**

## 📄 Licencja

MIT License - Zobacz LICENSE file dla szczegółów.