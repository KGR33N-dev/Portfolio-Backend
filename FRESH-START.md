# 🚀 Portfolio Backend - Fresh Start Guide

Ten przewodnik pomoże Ci rozpocząć pracę z Portfolio Backend od zera, niezależnie od tego czy masz już jakieś pozostałości z poprzednich instalacji.

## 🌟 Szybki Start (Polecane)

### 1. Sklonuj repozytorium
```bash
git clone https://github.com/KGR33N-dev/Portfolio-Backend.git
cd Portfolio-Backend
```

### 2. Uruchom automatyczny setup
```bash
chmod +x setup.sh
./setup.sh
```

### 3. Uruchom aplikację
```bash
cd backend
./start-fresh.sh
```

## 🧹 Co robi Fresh Start?

Skrypt `setup.sh` automatycznie:
- ✅ Wykrywa system operacyjny (Ubuntu/Debian/Amazon Linux/macOS)
- ✅ Instaluje Docker i Git (jeśli brakuje)
- ✅ **Usuwa wszystkie stare migracje** - to jest kluczowe!
- ✅ Czyści wszystkie kontenery Docker i woluminy
- ✅ Tworzy plik `.env` z bezpiecznymi domyślnymi ustawieniami
- ✅ Konfiguruje firewall na EC2 (jeśli wykryje AWS)

Skrypt `start-fresh.sh` dodatkowo:
- 🧹 Usuwa wszystkie kontenery i woluminy
- 🗑️ Czyści cache Python i Alembic
- 🚀 Buduje i uruchamia całą aplikację od zera

## 🔄 Automatyczne Migracje

Aplikacja automatycznie:
1. **Tworzy pierwszą migrację** jeśli nie ma żadnych plików migracji
2. **Uruchamia wszystkie migracje** na czystej bazie danych
3. **Startuje aplikację** - gotowa do utworzenia administratora

## 👑 Tworzenie Administratora

Po uruchomieniu aplikacji, utwórz administratora:

```bash
# Wejdź do kontenera
docker compose exec web bash

# Uruchom skrypt inicjalizacji
python app/create_admin.py
```

Skrypt automatycznie:
- ✅ Zainicjalizuje języki (EN, PL, DE, FR, ES)
- ✅ Utworzy role (user, moderator, admin)  
- ✅ Utworzy rangi (newbie → legend → vip)
- ✅ Zapyta o dane administratora (lub użyje ENV)
- ✅ Utworzy konto administratora z rangą VIP

### 🔧 Automatyzacja przez ENV

Możesz ustawić dane administratora w `.env`:

```bash
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure_password_123
ADMIN_FULL_NAME=Administrator
```

Jeśli te zmienne są ustawione, skrypt ich użyje bez pytania.

## 📁 Struktura po Fresh Start

```
backend/
├── alembic/versions/          # Nowe migracje będą tutaj
├── .env                       # Bezpieczna konfiguracja
├── docker-compose.yml         # Konfiguracja kontenerów
└── start-fresh.sh             # Skrypt do czystego startu
```

## 🌐 Dostęp do Aplikacji

Po uruchomieniu aplikacja będzie dostępna pod:
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs

### Logowanie Administratora:
- **Username**: admin (lub podany w ENV)
- **Password**: admin123 (lub podany w ENV)

### Na AWS EC2:
- **Backend API**: http://YOUR-EC2-IP:8000
- **API Documentation**: http://YOUR-EC2-IP:8000/api/docs

## 🔧 Rozwiązywanie Problemów

### Problem: "type userroleenum already exists"
**Rozwiązanie**: Uruchom fresh start
```bash
./setup.sh
cd backend
./start-fresh.sh
```

### Problem: Brak uprawnień Docker
**Rozwiązanie**: Wyloguj się i zaloguj ponownie
```bash
logout
# Zaloguj się ponownie
```

### Problem: Port 8000 zajęty
**Rozwiązanie**: Zabij procesy na porcie
```bash
sudo lsof -ti:8000 | xargs kill -9
```

## 🛠️ Ręczne Zarządzanie

### Utworzenie nowej migracji
```bash
cd backend
docker-compose exec web alembic revision --autogenerate -m "Your migration name"
```

### Uruchomienie migracji
```bash
cd backend
docker-compose exec web alembic upgrade head
```

### Sprawdzenie statusu migracji
```bash
cd backend
docker-compose exec web alembic current
```

## 📋 Wymagania Systemowe

- **Linux**: Ubuntu 18.04+, Debian 9+, Amazon Linux 2
- **macOS**: 10.14+
- **RAM**: Minimum 2GB
- **Dysk**: Minimum 5GB wolnego miejsca
- **Porty**: 8000, 5432 (dostępne)

## 🔐 Bezpieczeństwo

- Automatycznie generowany `SECRET_KEY`
- Bezpieczne hasła domyślne (zmień w produkcji!)
- Konfiguracja firewall na EC2
- Non-root user w kontenerach

## 📞 Wsparcie

Jeśli masz problemy:
1. Sprawdź logi: `docker-compose logs`
2. Zrestartuj: `./start-fresh.sh`
3. Sprawdź czy wszystkie porty są wolne
4. Upewnij się że masz wystarczająco RAM i miejsca na dysku

---

**💡 Tip**: Zawsze używaj `./start-fresh.sh` gdy chcesz rozpocząć od zera!
