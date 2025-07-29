# Portfolio Backend API Documentation

## 📋 Spis treści
- [Wprowadzenie](#wprowadzenie)
- [Autentykacja](#autentykacja)
- [Endpointy API](#endpointy-api)
  - [Autentykacja i użytkownicy](#autentykacja-i-użytkownicy)
  - [Blog](#blog)
  - [Klucze API](#klucze-api)
- [Modele danych](#modele-danych)
- [Kody błędów](#kody-błędów)
- [Przykłady użycia](#przykłady-użycia)

## 🔗 Wprowadzenie

Portfolio Backend API to REST API zbudowane z FastAPI, które obsługuje:
- System autentykacji z weryfikacją email
- Zarządzanie postami blogowymi
- System kluczy API
- Rate limiting i zabezpieczenia

**Base URL:** 
- Lokalne: `http://localhost:8000`
- Produkcja: `http://51.20.78.79:8000`

**Dokumentacja interaktywna:** `/api/docs`

## 🔐 Autentykacja

API używa JWT (JSON Web Tokens) do autentykacji. Obsługuje dwa typy tokenów:

### Access Token
- **Czas życia:** 30 minut
- **Użycie:** Autoryzacja żądań API
- **Header:** `Authorization: Bearer <access_token>`

### Refresh Token
- **Czas życia:** 7 dni
- **Użycie:** Odnawianie access tokenów

### Klucze API
Alternatywnie można używać kluczy API:
- **Header:** `X-API-Key: <your_api_key>`
- **Uprawnienia:** Konfigurowane per klucz

## 📚 Endpointy API

### Autentykacja i użytkownicy

#### 🔐 Rejestracja użytkownika
```http
POST /api/auth/register
```

**Body:**
```json
{
  "username": "string",
  "email": "user@example.com", 
  "password": "string",
  "full_name": "string",
  "bio": "string"
}
```

**Wymagania hasła:**
- Minimum 8 znaków
- Przynajmniej 1 wielka litera
- Przynajmniej 1 mała litera
- Przynajmniej 1 cyfra
- Przynajmniej 1 znak specjalny

**Odpowiedź:**
```json
{
  "success": true,
  "message": "Registration successful! Check your email for verification code",
  "data": {
    "email": "user@example.com",
    "expires_in_minutes": 15
  }
}
```

**Rate Limit:** 3 żądania/godzinę na IP

---

#### ✅ Weryfikacja email
```http
POST /api/auth/verify-email
```

**Body:**
```json
{
  "email": "user@example.com",
  "verification_code": "123456"
}
```

**Odpowiedź:**
```json
{
  "success": true,
  "message": "Email verified successfully! You can now log in.",
  "data": {
    "user_id": 1,
    "email_verified": true
  }
}
```

---

#### 📧 Ponowne wysłanie kodu weryfikacyjnego
```http
POST /api/auth/resend-verification
```

**Body:**
```json
{
  "email": "user@example.com"
}
```

---

#### 🚪 Logowanie
```http
POST /api/auth/login
```

**Content-Type:** `application/x-www-form-urlencoded`

**Body:**
```
username=user@example.com&password=your_password
```

**Uwaga:** W polu `username` należy podać email (standard OAuth2)

**Odpowiedź:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "user@example.com",
    "full_name": "Test User",
    "bio": null,
    "is_active": true,
    "is_admin": false,
    "email_verified": true,
    "created_at": "2025-01-20T10:00:00"
  }
}
```

**Rate Limit:** 5 żądań/15 minut na IP

---

#### 🔄 Odnawianie tokenu
```http
POST /api/auth/refresh
```

**Body:**
```json
{
  "refresh_token": "your_refresh_token"
}
```

---

#### 👤 Profil użytkownika
```http
GET /api/auth/me
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Odpowiedź:**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "user@example.com",
  "full_name": "Test User",
  "bio": "My bio",
  "is_active": true,
  "is_admin": false,
  "email_verified": true,
  "created_at": "2025-01-20T10:00:00"
}
```

---

### Blog

#### 📝 Lista postów (publiczne)
```http
GET /api/blog/
```

**Parametry query:**
- `page` (int): Numer strony (domyślnie 1)
- `per_page` (int): Ilość postów na stronę (domyślnie 10, max 50)
- `category` (string): Filtrowanie po kategorii
- `language` (string): Filtrowanie po języku (pl/en)
- `search` (string): Wyszukiwanie w tytule i contencie

**Odpowiedź:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Tytuł posta",
      "content": "Treść posta...",
      "excerpt": "Krótki opis...",
      "slug": "tytul-posta",
      "author": "KGR33N",
      "category": "programming",
      "language": "pl",
      "is_published": true,
      "published_at": "2025-01-20T10:00:00",
      "created_at": "2025-01-20T10:00:00",
      "updated_at": "2025-01-20T10:00:00",
      "tags": ["javascript", "tutorial"],
      "meta_title": "SEO tytuł",
      "meta_description": "SEO opis"
    }
  ],
  "total": 25,
  "page": 1,
  "pages": 3,
  "per_page": 10
}
```

---

#### 📖 Pojedynczy post
```http
GET /api/blog/{slug}
```

**Parametry:**
- `slug` (string): Unikalny identyfikator posta

---

#### 📝 Tworzenie posta (Admin)
```http
POST /api/blog/
```

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Body:**
```json
{
  "title": "Tytuł nowego posta",
  "content": "Pełna treść posta...",
  "excerpt": "Krótki opis posta",
  "slug": "tytul-nowego-posta",
  "category": "programming",
  "language": "pl",
  "tags": ["javascript", "tutorial"],
  "meta_title": "SEO tytuł",
  "meta_description": "SEO opis"
}
```

**Rate Limit:** 20 żądań/godzinę dla adminów

---

#### ✏️ Edycja posta (Admin)
```http
PUT /api/blog/{id}
```

**Parametry:**
- `id` (int): ID posta

**Body:** Jak przy tworzeniu (wszystkie pola opcjonalne)

---

#### 🗑️ Usuwanie posta (Admin)
```http
DELETE /api/blog/{id}
```

---

#### 📊 Publikowanie/ukrywanie posta (Admin)
```http
POST /api/blog/{id}/publish
POST /api/blog/{id}/unpublish
```

---

### Klucze API

#### 🔑 Tworzenie klucza API (Admin)
```http
POST /api/auth/api-keys
```

**Body:**
```json
{
  "name": "Frontend App",
  "permissions": ["read", "write"],
  "expires_days": 30
}
```

**Odpowiedź:**
```json
{
  "api_key": {
    "id": 1,
    "name": "Frontend App",
    "key_preview": "sk_live_abc123...",
    "permissions": ["read", "write"],
    "created_at": "2025-01-20T10:00:00",
    "expires_at": "2025-02-20T10:00:00",
    "is_active": true
  },
  "full_key": "sk_live_abc123def456ghi789jkl012mno345pqr678stu901vwx234"
}
```

---

#### 📋 Lista kluczy API (Admin)
```http
GET /api/auth/api-keys
```

---

#### 🗑️ Usuwanie klucza API (Admin)
```http
DELETE /api/auth/api-keys/{id}
```

---

## 🗄️ Modele danych

### User
```json
{
  "id": "integer",
  "username": "string",
  "email": "string", 
  "full_name": "string | null",
  "bio": "string | null",
  "is_active": "boolean",
  "is_admin": "boolean", 
  "email_verified": "boolean",
  "created_at": "datetime"
}
```

### BlogPost
```json
{
  "id": "integer",
  "title": "string",
  "content": "string",
  "excerpt": "string | null",
  "slug": "string",
  "author": "string",
  "category": "string",
  "language": "pl | en",
  "is_published": "boolean",
  "published_at": "datetime | null",
  "created_at": "datetime",
  "updated_at": "datetime",
  "tags": "string[]",
  "meta_title": "string | null",
  "meta_description": "string | null"
}
```

### APIKey
```json
{
  "id": "integer",
  "name": "string",
  "key_preview": "string",
  "permissions": "string[]",
  "created_at": "datetime",
  "expires_at": "datetime | null",
  "is_active": "boolean"
}
```

---

## ❌ Kody błędów

### HTTP Status Codes

| Kod | Znaczenie | Opis |
|-----|-----------|------|
| 200 | OK | Żądanie zakończone sukcesem |
| 201 | Created | Zasób został utworzony |
| 400 | Bad Request | Nieprawidłowe dane wejściowe |
| 401 | Unauthorized | Brak autoryzacji |
| 403 | Forbidden | Brak uprawnień |
| 404 | Not Found | Zasób nie znaleziony |
| 422 | Unprocessable Entity | Błędy walidacji |
| 423 | Locked | Konto zablokowane |
| 429 | Too Many Requests | Przekroczony rate limit |
| 500 | Internal Server Error | Błąd serwera |

### Typowe błędy

#### Błędy autentykacji
```json
{
  "detail": "Could not validate credentials"
}
```

#### Błędy walidacji
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "input": "abc123"
    }
  ]
}
```

#### Rate limiting
```json
{
  "detail": "Rate limit exceeded: 5 per 15 minutes"
}
```

#### Konto zablokowane
```json
{
  "detail": "Account locked. Try again in 25 minutes."
}
```

---

## 💡 Przykłady użycia

### Pełny workflow rejestracji i logowania

#### 1. Rejestracja
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }'
```

#### 2. Weryfikacja email (kod z email)
```bash
curl -X POST "http://localhost:8000/api/auth/verify-email" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "verification_code": "123456"
  }'
```

#### 3. Logowanie
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=SecurePass123!"
```

#### 4. Użycie tokenu
```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Praca z blogiem

#### Pobranie postów
```bash
curl -X GET "http://localhost:8000/api/blog/?page=1&per_page=5&category=programming"
```

#### Utworzenie posta (admin)
```bash
curl -X POST "http://localhost:8000/api/blog/" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Nowy post o JavaScript",
    "content": "Treść posta...",
    "slug": "nowy-post-javascript",
    "category": "programming",
    "tags": ["javascript", "tutorial"]
  }'
```

### Klucze API

#### Utworzenie klucza
```bash
curl -X POST "http://localhost:8000/api/auth/api-keys" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Frontend App",
    "permissions": ["read"],
    "expires_days": 30
  }'
```

#### Użycie klucza API
```bash
curl -X GET "http://localhost:8000/api/blog/" \
  -H "X-API-Key: sk_live_abc123def456..."
```

---

## 🔧 Rate Limiting

| Endpoint | Limit | Okres |
|----------|-------|-------|
| `/api/auth/register` | 3 żądania | 1 godzina |
| `/api/auth/login` | 5 żądań | 15 minut |
| `/api/auth/verify-email` | 10 żądań | 1 godzina |
| `/api/auth/resend-verification` | 3 żądania | 1 godzina |
| Blog endpoints (read) | 100 żądań | 1 godzina |
| Blog endpoints (write, admin) | 20 żądań | 1 godzina |
| General API | 1000 żądań | 1 godzina |

---

## 🛡️ Bezpieczeństwo

### Zabezpieczenia implementowane:
- **HTTPS w produkcji**
- **JWT tokeny z krótkim czasem życia**
- **Bcrypt do hashowania haseł (12 rounds)**
- **Rate limiting na krytycznych endpointach**
- **Walidacja i sanityzacja danych wejściowych**
- **CORS skonfigurowany dla konkretnych domen**
- **Blokada konta po nieudanych próbach logowania**
- **Weryfikacja email przed aktywacją konta**
- **Bezpieczne nagłówki HTTP**

### Zalecenia dla klientów:
- Przechowuj tokeny bezpiecznie (nie w localStorage w przypadku XSS)
- Implementuj refresh token rotation
- Używaj HTTPS w produkcji
- Waliduj dane po stronie klienta
- Implementuj proper error handling

---

## 📞 Wsparcie

W przypadku problemów lub pytań:
- Sprawdź interaktywną dokumentację: `/api/docs`
- Sprawdź status API: `/api/health`
- Kontakt: [email lub inne informacje kontaktowe]

---

**Wersja dokumentacji:** 1.0.0  
**Ostatnia aktualizacja:** Styczeń 2025  
**API Version:** 1.0.0
