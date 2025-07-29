# 🚀 Portfolio Backend

Nowoczesne REST API zbudowane z FastAPI dla portfolio KGR33N z systemem weryfikacji email i zaawansowanymi funkcjami bezpieczeństwa.

## ✨ Funkcje

- 🔐 **System autentykacji JWT** z weryfikacją email
- 📧 **Weryfikacja email** z 6-cyfrowymi kodami
- 🛡️ **Zaawansowane bezpieczeństwo** (rate limiting, blokada konta, silne hasła)
- 📝 **System blogowy** z tagami i kategoriami
- 🔑 **Klucze API** z konfigurowalnymi uprawnieniami
- 🐳 **Docker** gotowy do produkcji
- 📚 **Kompletna dokumentacja** API
- 🌍 **CORS** skonfigurowany dla frontend
- ⚡ **Rate limiting** dla ochrony przed nadużyciami
- 🔄 **Refresh tokeny** dla bezpiecznej sesji

## 🛠️ Tech Stack

- **FastAPI** - Nowoczesny framework web
- **PostgreSQL** - Baza danych
- **SQLAlchemy** - ORM
- **Alembic** - Migracje bazy danych
- **JWT** - Autentykacja
- **Bcrypt** - Hashowanie haseł
- **Docker** - Konteneryzacja
- **Pydantic** - Walidacja danych
- **SlowAPI** - Rate limiting

## 🚀 Szybki start

### Wymagania
- Docker & Docker Compose
- Git

### 1. Klonowanie repozytorium
```bash
git clone https://github.com/KGR33N-dev/Portfolio-Backend.git
cd Portfolio-Backend
```

### 2. Uruchomienie lokalnie
```bash
cd backend
chmod +x start-local.sh
./start-local.sh
```

### 3. Sprawdzenie czy działa
```bash
curl http://localhost:8000/api/health
```

### 4. Dokumentacja API
Otwórz w przeglądarce: http://localhost:8000/api/docs

## 📋 Szczegółowa instrukcja

### Zmienne środowiskowe

Utwórz plik `.env` w folderze `backend/`:

```env
# Database
DATABASE_URL=postgresql://postgres:password@db:5432/portfolio
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=portfolio

# Security
SECRET_KEY=your-super-secret-key-change-in-production-64-chars-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Admin account (opcjonalne)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-admin-password

# Email (do implementacji)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Uruchomienie w trybie development

```bash
cd backend

# Uruchomienie z Docker Compose
docker compose up --build

# Lub bez buildu
docker compose up -d

# Sprawdzenie logów
docker compose logs -f web
```

### Uruchomienie w trybie production

```bash
cd backend

# Deployment na AWS/VPS
./deploy.sh deploy

# Lub ręcznie
docker compose -f docker-compose.prod.yml up --build -d
```

## 🗄️ Baza danych

### Migracje

```bash
# Tworzenie nowej migracji
docker compose exec web alembic revision --autogenerate -m "Description"

# Zastosowanie migracji
docker compose exec web alembic upgrade head

# Sprawdzenie obecnej wersji
docker compose exec web alembic current
```

### Bezpośrednie połączenie z bazą

```bash
docker compose exec db psql -U postgres -d portfolio
```

### Czyszczenie bazy danych

```bash
docker compose down -v  # Usuwa volumeny z danymi
docker compose up --build -d
```

## 👤 Zarządzanie użytkownikami

### Tworzenie konta administratora

```bash
# Automatycznie z zmiennych środowiskowych
docker compose exec web python -m app.create_admin

# Lub ręcznie
docker compose exec web python -c "
from app.database import SessionLocal
from app.security import get_password_hash
from app.models import User
from datetime import datetime

db = SessionLocal()
admin = User(
    username='admin',
    email='admin@example.com',
    hashed_password=get_password_hash('your-password'),
    full_name='Administrator',
    is_active=True,
    is_admin=True,
    email_verified=True
)
db.add(admin)
db.commit()
print('Admin created!')
"
```

### Reset hasła administratora

```bash
docker compose exec web python -c "
from app.database import SessionLocal
from app.security import get_password_hash
from app.models import User

db = SessionLocal()
admin = db.query(User).filter(User.email == 'admin@example.com').first()
if admin:
    admin.hashed_password = get_password_hash('new-password')
    db.commit()
    print('Password updated!')
else:
    print('Admin not found!')
"
```

## 🔧 Konfiguracja

### CORS Origins

W `app/main.py` zaktualizuj listę dozwolonych origins:

```python
origins = [
    "http://localhost:3000",    # React dev
    "http://localhost:4321",    # Astro dev
    "https://yourdomain.com",   # Production frontend
    # ... inne domeny
]
```

### Rate Limiting

Dostosuj limity w `app/security.py`:

```python
@rate_limit_by_ip(requests=5, period=900)  # 5 żądań na 15 minut
def strict_rate_limit_login():
    pass
```

### Email Configuration

Zaktualizuj `send_verification_email()` w `app/security.py`:

```python
async def send_verification_email(email: str, verification_code: str, verification_token: str) -> bool:
    # Implementacja z Twojym providerem email (SendGrid, AWS SES, etc.)
    pass
```

## 📊 Monitoring i logi

### Sprawdzenie statusu
```bash
curl http://localhost:8000/api/health
```

### Logi aplikacji
```bash
docker compose logs -f web
```

### Logi bazy danych
```bash
docker compose logs -f db
```

### Metryki kontenerów
```bash
docker stats
```

## 🧪 Testowanie

### Endpoint testing z curl

```bash
# Health check
curl http://localhost:8000/api/health

# Rejestracja
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }'

# Logowanie
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=SecurePass123!"

# Blog posts
curl http://localhost:8000/api/blog/
```

### Testowanie z Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/api/health")
print(response.json())

# Rejestracja
register_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
}
response = requests.post("http://localhost:8000/api/auth/register", json=register_data)
print(response.json())
```

## 🔒 Bezpieczeństwo

### Checklist bezpieczeństwa

- [ ] Zmień `SECRET_KEY` na produkcji
- [ ] Używaj HTTPS w produkcji
- [ ] Skonfiguruj firewall (tylko porty 80, 443, 22)
- [ ] Regularnie aktualizuj dependencies
- [ ] Monitoruj logi pod kątem ataków
- [ ] Skonfiguruj backup bazy danych
- [ ] Używaj silnych haseł dla adminów
- [ ] Skonfiguruj email provider
- [ ] Zastosuj SSL dla bazy danych w produkcji

### Zalecane zmienne środowiskowe produkcyjne

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=64-character-random-string
DATABASE_URL=postgresql://user:password@prod-db:5432/portfolio
FRONTEND_URL=https://yourdomain.com
```

## 📂 Struktura projektu

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Główna aplikacja FastAPI
│   ├── database.py          # Konfiguracja bazy danych
│   ├── models.py            # Modele SQLAlchemy
│   ├── schemas.py           # Schematy Pydantic
│   ├── security.py          # Funkcje bezpieczeństwa
│   ├── create_admin.py      # Skrypt tworzenia admina
│   └── routers/
│       ├── __init__.py
│       ├── auth.py          # Endpointy autentykacji
│       └── blog.py          # Endpointy bloga
├── alembic/                 # Migracje bazy danych
├── docker-compose.yml       # Development
├── docker-compose.prod.yml  # Production
├── Dockerfile
├── requirements.txt
├── start-local.sh          # Skrypt uruchomienia lokalnego
└── deploy.sh              # Skrypt deploymentu
```

## 🚀 Deployment

### AWS EC2

1. **Przygotowanie serwera:**
```bash
# Aktualizacja systemu
sudo apt update && sudo apt upgrade -y

# Instalacja Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalacja Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Deployment:**
```bash
git clone https://github.com/KGR33N-dev/Portfolio-Backend.git
cd Portfolio-Backend/backend
chmod +x deploy.sh
./deploy.sh deploy
```

3. **Nginx Proxy (opcjonalne):**
```bash
sudo apt install nginx
sudo nano /etc/nginx/sites-available/portfolio-api

# Konfiguracja nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

sudo ln -s /etc/nginx/sites-available/portfolio-api /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## 📚 Dokumentacja

- **[API Documentation](API-DOCS.md)** - Kompletna dokumentacja endpointów
- **[Interactive Docs](http://localhost:8000/api/docs)** - Swagger UI
- **[ReDoc](http://localhost:8000/api/redoc)** - Alternatywna dokumentacja

## 🤝 Contributing

1. Fork projektu
2. Stwórz branch feature (`git checkout -b feature/AmazingFeature`)
3. Commit zmian (`git commit -m 'Add some AmazingFeature'`)
4. Push do brancha (`git push origin feature/AmazingFeature`)
5. Otwórz Pull Request

## 📝 Changelog

### v1.0.0 (2025-01-29)
- ✨ Kompletny system weryfikacji email
- 🔐 JWT authentication z refresh tokenami
- 📝 System blogowy z tagami
- 🔑 API keys z uprawnieniami
- 🛡️ Zaawansowane zabezpieczenia
- 🐳 Docker configuration
- 📚 Kompletna dokumentacja

## 📄 Licencja

Ten projekt jest licencjonowany na podstawie MIT License - zobacz plik [LICENSE](LICENSE) po szczegóły.

## 👨‍💻 Autor

**KGR33N** - [GitHub](https://github.com/KGR33N-dev)

## 🙏 Podziękowania

- FastAPI za wspaniały framework
- Community za inspirację i pomoc
- Wszyscy kontrybutorzy

---

**Made with ❤️ by KGR33N**
