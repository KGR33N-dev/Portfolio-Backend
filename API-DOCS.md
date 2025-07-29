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

## 📝 Instrukcje dla Frontend Developer - Zarządzanie Blogiem

### 🎯 Zasady i workflow

#### Kto może zarządzać blogiem?
- **Tylko administratorzy** mogą tworzyć, edytować i usuwać posty
- **Publiczne API** umożliwia czytanie postów wszystkim użytkownikom
- **Rate limiting**: Admini mają wyższe limity (20 żądań/godzinę vs 100 żądań/godzinę dla czytania)

#### Wymagane uprawnienia
```typescript
// Sprawdzenie czy użytkownik jest adminem
const user = await apiClient.getProfile();
if (!user.is_admin) {
  throw new Error('Admin permissions required');
}
```

### 📋 Workflow tworzenia posta

#### 1. Przygotowanie danych
```typescript
interface BlogPostData {
  title: string;           // Wymagane - tytuł posta
  content: string;         // Wymagane - pełna treść (HTML/Markdown)
  slug: string;           // Wymagane - unikalny URL (kebab-case)
  excerpt?: string;       // Opcjonalne - krótki opis
  category?: string;      // Opcjonalne - kategoria (domyślnie "general")
  language?: 'pl' | 'en'; // Opcjonalne - język (domyślnie "pl")
  tags?: string[];        // Opcjonalne - lista tagów
  meta_title?: string;    // Opcjonalne - SEO tytuł
  meta_description?: string; // Opcjonalne - SEO opis
}
```

#### 2. Walidacja po stronie frontend
```typescript
function validateBlogPost(data: BlogPostData): string[] {
  const errors: string[] = [];
  
  // Tytuł
  if (!data.title || data.title.trim().length === 0) {
    errors.push('Tytuł jest wymagany');
  }
  if (data.title && data.title.length > 200) {
    errors.push('Tytuł nie może być dłuższy niż 200 znaków');
  }
  
  // Treść
  if (!data.content || data.content.trim().length === 0) {
    errors.push('Treść jest wymagana');
  }
  
  // Slug
  if (!data.slug || data.slug.trim().length === 0) {
    errors.push('Slug jest wymagany');
  }
  if (data.slug && data.slug.length > 200) {
    errors.push('Slug nie może być dłuższy niż 200 znaków');
  }
  if (data.slug && !/^[a-z0-9-]+$/.test(data.slug)) {
    errors.push('Slug może zawierać tylko małe litery, cyfry i myślniki');
  }
  
  // Język
  if (data.language && !['pl', 'en'].includes(data.language)) {
    errors.push('Język musi być "pl" lub "en"');
  }
  
  return errors;
}
```

#### 3. Generowanie slug automatycznie
```typescript
function generateSlug(title: string): string {
  return title
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '') // Usuń znaki specjalne
    .replace(/\s+/g, '-')         // Spacje na myślniki
    .replace(/-+/g, '-')          // Wielokrotne myślniki na jeden
    .replace(/^-|-$/g, '');       // Usuń myślniki z początku i końca
}

// Przykład użycia
const title = "Nowy post o JavaScript!";
const slug = generateSlug(title); // "nowy-post-o-javascript"
```

#### 4. Tworzenie posta
```typescript
async function createBlogPost(postData: BlogPostData) {
  try {
    // Walidacja
    const errors = validateBlogPost(postData);
    if (errors.length > 0) {
      throw new Error(`Błędy walidacji: ${errors.join(', ')}`);
    }
    
    // Wysłanie do API
    const response = await apiClient.createBlogPost(postData);
    
    console.log('Post utworzony:', response);
    return response;
    
  } catch (error) {
    if (error.status === 409) {
      throw new Error('Post o tym slug już istnieje');
    }
    if (error.status === 403) {
      throw new Error('Brak uprawnień administratora');
    }
    throw error;
  }
}
```

### ✏️ Edycja istniejących postów

#### 1. Pobranie posta do edycji
```typescript
async function getPostForEdit(id: number) {
  try {
    const post = await apiClient.getBlogPostById(id);
    
    // Sprawdź czy użytkownik może edytować
    const user = await apiClient.getProfile();
    if (!user.is_admin) {
      throw new Error('Tylko admin może edytować posty');
    }
    
    return post;
  } catch (error) {
    console.error('Błąd pobierania posta:', error);
    throw error;
  }
}
```

#### 2. Aktualizacja posta
```typescript
async function updateBlogPost(id: number, updates: Partial<BlogPostData>) {
  try {
    // Tylko pola które się zmieniły
    const response = await apiClient.updateBlogPost(id, updates);
    
    console.log('Post zaktualizowany:', response);
    return response;
    
  } catch (error) {
    if (error.status === 404) {
      throw new Error('Post nie znaleziony');
    }
    if (error.status === 409) {
      throw new Error('Slug już zajęty przez inny post');
    }
    throw error;
  }
}
```

### 📊 Zarządzanie publikacją

#### Publikowanie/ukrywanie postów
```typescript
async function togglePostPublication(id: number, publish: boolean) {
  try {
    if (publish) {
      await apiClient.publishPost(id);
      console.log('Post opublikowany');
    } else {
      await apiClient.unpublishPost(id);
      console.log('Post ukryty');
    }
  } catch (error) {
    console.error('Błąd zmiany statusu publikacji:', error);
    throw error;
  }
}
```

### 🗑️ Usuwanie postów

```typescript
async function deleteBlogPost(id: number) {
  try {
    // Potwierdzenie przed usunięciem
    const confirmed = confirm('Czy na pewno chcesz usunąć ten post? Ta operacja jest nieodwracalna.');
    
    if (confirmed) {
      await apiClient.deleteBlogPost(id);
      console.log('Post usunięty');
      return true;
    }
    
    return false;
  } catch (error) {
    if (error.status === 404) {
      throw new Error('Post nie znaleziony');
    }
    throw error;
  }
}
```

### 🏷️ Zarządzanie tagami

#### Popularne tagi (pobieranie z istniejących postów)
```typescript
async function getPopularTags(): Promise<string[]> {
  try {
    // Pobierz wszystkie posty i wyciągnij tagi
    const response = await apiClient.getBlogPosts({ per_page: 100 });
    const allTags = response.items.flatMap(post => post.tags || []);
    
    // Zlicz wystąpienia
    const tagCounts = allTags.reduce((acc, tag) => {
      acc[tag] = (acc[tag] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    // Sortuj po popularności
    return Object.entries(tagCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 20) // Top 20
      .map(([tag]) => tag);
      
  } catch (error) {
    console.error('Błąd pobierania tagów:', error);
    return [];
  }
}
```

#### Walidacja tagów
```typescript
function validateTags(tags: string[]): string[] {
  return tags
    .filter(tag => tag.trim().length > 0)
    .map(tag => tag.trim().toLowerCase())
    .filter(tag => tag.length <= 50)
    .slice(0, 10); // Maksymalnie 10 tagów
}
```

### 📱 Przykład React komponenta dla tworzenia posta

```tsx
import React, { useState } from 'react';

interface BlogPostFormProps {
  onSubmit: (data: BlogPostData) => Promise<void>;
  initialData?: Partial<BlogPostData>;
  isEditing?: boolean;
}

export function BlogPostForm({ onSubmit, initialData, isEditing }: BlogPostFormProps) {
  const [formData, setFormData] = useState<BlogPostData>({
    title: initialData?.title || '',
    content: initialData?.content || '',
    slug: initialData?.slug || '',
    excerpt: initialData?.excerpt || '',
    category: initialData?.category || 'programming',
    language: initialData?.language || 'pl',
    tags: initialData?.tags || [],
    meta_title: initialData?.meta_title || '',
    meta_description: initialData?.meta_description || '',
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  const handleTitleChange = (title: string) => {
    setFormData(prev => ({
      ...prev,
      title,
      slug: !isEditing && !prev.slug ? generateSlug(title) : prev.slug
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationErrors = validateBlogPost(formData);
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }
    
    setIsSubmitting(true);
    setErrors([]);
    
    try {
      await onSubmit(formData);
    } catch (error) {
      setErrors([error.message]);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Tytuł */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Tytuł *
        </label>
        <input
          type="text"
          value={formData.title}
          onChange={(e) => handleTitleChange(e.target.value)}
          className="w-full p-3 border rounded-lg"
          placeholder="Wprowadź tytuł posta"
          required
        />
      </div>

      {/* Slug */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Slug URL *
        </label>
        <input
          type="text"
          value={formData.slug}
          onChange={(e) => setFormData(prev => ({ ...prev, slug: e.target.value }))}
          className="w-full p-3 border rounded-lg font-mono text-sm"
          placeholder="url-friendly-slug"
          pattern="^[a-z0-9-]+$"
          required
        />
        <p className="text-xs text-gray-500 mt-1">
          Tylko małe litery, cyfry i myślniki. URL: /blog/{formData.slug}
        </p>
      </div>

      {/* Kategoria i język */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">
            Kategoria
          </label>
          <select
            value={formData.category}
            onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
            className="w-full p-3 border rounded-lg"
          >
            <option value="programming">Programming</option>
            <option value="tutorial">Tutorial</option>
            <option value="personal">Personal</option>
            <option value="news">News</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2">
            Język
          </label>
          <select
            value={formData.language}
            onChange={(e) => setFormData(prev => ({ ...prev, language: e.target.value as 'pl' | 'en' }))}
            className="w-full p-3 border rounded-lg"
          >
            <option value="pl">Polski</option>
            <option value="en">English</option>
          </select>
        </div>
      </div>

      {/* Treść */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Treść *
        </label>
        <textarea
          value={formData.content}
          onChange={(e) => setFormData(prev => ({ ...prev, content: e.target.value }))}
          className="w-full p-3 border rounded-lg h-96"
          placeholder="Napisz treść posta... (obsługuje HTML i Markdown)"
          required
        />
      </div>

      {/* Excerpt */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Krótki opis
        </label>
        <textarea
          value={formData.excerpt}
          onChange={(e) => setFormData(prev => ({ ...prev, excerpt: e.target.value }))}
          className="w-full p-3 border rounded-lg h-24"
          placeholder="Krótki opis posta dla listy i SEO"
        />
      </div>

      {/* Tagi */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Tagi
        </label>
        <input
          type="text"
          value={formData.tags?.join(', ') || ''}
          onChange={(e) => setFormData(prev => ({ 
            ...prev, 
            tags: validateTags(e.target.value.split(','))
          }))}
          className="w-full p-3 border rounded-lg"
          placeholder="javascript, tutorial, react (oddziel przecinkami)"
        />
        <p className="text-xs text-gray-500 mt-1">
          Maksymalnie 10 tagów, każdy do 50 znaków
        </p>
      </div>

      {/* SEO */}
      <details className="bg-gray-50 p-4 rounded-lg">
        <summary className="font-medium cursor-pointer">
          Ustawienia SEO (opcjonalne)
        </summary>
        <div className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              SEO Tytuł
            </label>
            <input
              type="text"
              value={formData.meta_title}
              onChange={(e) => setFormData(prev => ({ ...prev, meta_title: e.target.value }))}
              className="w-full p-3 border rounded-lg"
              placeholder="Tytuł dla wyszukiwarek (jeśli inny niż główny)"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">
              SEO Opis
            </label>
            <textarea
              value={formData.meta_description}
              onChange={(e) => setFormData(prev => ({ ...prev, meta_description: e.target.value }))}
              className="w-full p-3 border rounded-lg h-20"
              placeholder="Opis dla wyszukiwarek (150-160 znaków)"
              maxLength={160}
            />
          </div>
        </div>
      </details>

      {/* Błędy */}
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h4 className="text-red-800 font-medium mb-2">Błędy walidacji:</h4>
          <ul className="text-red-700 text-sm space-y-1">
            {errors.map((error, index) => (
              <li key={index}>• {error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Przyciski */}
      <div className="flex gap-4">
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Zapisywanie...' : (isEditing ? 'Zaktualizuj' : 'Utwórz post')}
        </button>
        
        <button
          type="button"
          onClick={() => window.history.back()}
          className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
        >
          Anuluj
        </button>
      </div>
    </form>
  );
}
```

### 🚨 Ważne zasady

1. **Zawsze sprawdzaj uprawnienia** przed pokazaniem interfejsu admina
2. **Waliduj dane po stronie frontend** przed wysłaniem do API
3. **Obsługuj błędy gracefully** z przyjaznym komunikatem
4. **Generuj slug automatycznie** z tytułu, ale pozwól na edycję
5. **Ogranicz liczbę tagów** do maksymalnie 10
6. **Używaj rate limitingu** - nie wysyłaj zbyt często żądań
7. **Implementuj auto-save** dla długich formularzy
8. **Pokazuj podgląd** przed publikacją

### 💾 Zapisywanie wersji roboczych

```typescript
// Auto-save co 30 sekund
useEffect(() => {
  const interval = setInterval(() => {
    if (formData.title || formData.content) {
      localStorage.setItem('blog-draft', JSON.stringify(formData));
    }
  }, 30000);

  return () => clearInterval(interval);
}, [formData]);

// Przywracanie wersji roboczej
useEffect(() => {
  const draft = localStorage.getItem('blog-draft');
  if (draft) {
    const parsed = JSON.parse(draft);
    setFormData(parsed);
  }
}, []);
```

---

**Wersja dokumentacji:** 1.0.0  
**Ostatnia aktualizacja:** Styczeń 2025  
**API Version:** 1.0.0
