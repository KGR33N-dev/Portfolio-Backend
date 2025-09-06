# 🚀 Uruchamianie Portfolio Backend z Alembic

## Przygotowanie projektu z Alembic migrations

Ten projekt został skonfigurowany z Alembic do zarządzania migracjami bazy danych.

### 📋 Wymagania

- Docker i Docker Compose
- Python 3.12+ (jeśli chcesz uruchamiać lokalnie)

### 🐳 Uruchamianie z Docker Compose (Zalecane)

#### Opcja 1: Szybkie uruchomienie z czystą bazą danych

```bash
# Przejdź do katalogu backend
cd backend

# Uruchom skrypt czyszczenia i startu
./start-fresh.sh
```

#### Opcja 2: Standardowe uruchomienie

```bash
cd backend

# Zatrzymaj stare kontenery i wyczyść woluminy
docker-compose down -v

# Uruchom z nową bazą danych
docker-compose up --build
```

### 🔧 Uruchamianie lokalne (Development)

1. **Uruchom tylko bazę danych z Docker:**
```bash
cd backend
docker-compose up db -d
```

2. **Skonfiguruj zmienne środowiskowe:**
```bash
# Skopiuj .env dla lokalnego rozwoju
cp .env.local .env
```

3. **Uruchom migracje:**
```bash
# Aktywuj wirtualne środowisko
source ../.venv/bin/activate

# Uruchom migracje
alembic upgrade head

# Zainicjalizuj dane domyślne
python init-data.py
```

4. **Uruchom aplikację:**
```bash
uvicorn app.main:app --reload
```

### 📊 Zarządzanie migracjami

#### Tworzenie nowej migracji
```bash
# Po zmianach w modelach
alembic revision --autogenerate -m "Opis zmian"
```

#### Aplikowanie migracji
```bash
alembic upgrade head
```

#### Wycofanie migracji
```bash
alembic downgrade -1  # Cofnij o jedną migrację
alembic downgrade base  # Cofnij wszystkie migracje
```

#### Sprawdzenie statusu migracji
```bash
alembic current
alembic history
```

### 🗄️ Struktura bazy danych

Po uruchomieniu migracji zostają utworzone następujące tabele:

- **user_roles** - Role użytkowników (user, moderator, admin)
- **user_ranks** - Rangi/odznaczenia (newbie, regular, trusted, star, legend, vip)
- **users** - Użytkownicy z pełnym systemem bezpieczeństwa
- **languages** - Dostępne języki dla postów
- **blog_posts** - Posty bloga (wielojęzyczne)
- **blog_post_translations** - Tłumaczenia postów
- **blog_tags** - Tagi dla postów
- **comments** - Komentarze do postów
- **comment_likes** - Polubienia komentarzy
- **api_keys** - Klucze API
- **votes** - System głosowań/ankiet

### 🌱 Dane domyślne

Po pierwszym uruchomieniu automatycznie tworzone są:

#### Języki:
- English (en)
- Polski (pl)

#### Role użytkowników:
- **user** - Zwykły użytkownik
- **admin** - Administrator

#### Rangi użytkowników:
- **newbie** - 👶 Nowy użytkownik
- **regular** - 👤 Regularny użytkownik  
- **trusted** - 🤝 Zaufany użytkownik
- **star** - ⭐ Gwiazda społeczności

### 🔍 Rozwiązywanie problemów

#### Problem z połączeniem do bazy danych
```bash
# Sprawdź czy kontener bazy działa
docker-compose ps

# Sprawdź logi bazy danych
docker-compose logs db
```

#### Problem z migracjami
```bash
# Sprawdź status migracji
alembic current

# Sprawdź historię
alembic history --verbose
```

#### Reset całego systemu
```bash
# Zatrzymaj wszystko i wyczyść
docker-compose down -v
docker volume prune -f

# Uruchom ponownie
./start-fresh.sh
```

### 📝 Zmienne środowiskowe

Ważne zmienne w pliku `.env`:

```env
# Baza danych
DATABASE_URL=postgresql://postgres:password@db:5432/portfolio
POSTGRES_DB=portfolio
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Aplikacja
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
DEBUG=True

# Frontend
FRONTEND_URL=http://localhost:4321
```

### 🎯 API Documentation

Po uruchomieniu dokumentacja API dostępna pod:
- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

### 🛡️ Bezpieczeństwo

- Kontenery uruchamiane jako użytkownik `app` (nie root)
- Pełny system autentykacji z JWT
- Rate limiting dla API
- Weryfikacja email
- System blokowania kont po nieudanych logowaniach
- Haszowanie haseł z bcrypt

### 🚀 Production Deployment

Dla produkcji użyj `docker-compose.prod.yml`:

```bash
docker-compose -f docker-compose.prod.yml up -d
```
