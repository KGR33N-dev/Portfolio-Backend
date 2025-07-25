# 🚀 Krok po kroku - Deployment Portfolio Backend

## ✅ Twoja konfiguracja:
- **EC2 IP:** 51.20.78.79 (eu-north-1)
- **Frontend:** https://kgr33n.com (Cloudflare Pages)
- **Repository:** https://github.com/KGR33N-dev/Portfolio-Backend

## 📝 **KROK 1: GitHub Secrets (5 min)**

1. Idź do: https://github.com/KGR33N-dev/Portfolio-Backend/settings/secrets/actions

2. Kliknij "New repository secret" i dodaj każdy z poniższych:

```
EC2_HOST
Value: 51.20.78.79

EC2_USER  
Value: ec2-user

EC2_SSH_KEY
Value: [Wklej całą zawartość twojego prywatnego klucza SSH - od -----BEGIN do -----END]

DATABASE_URL
Value: postgresql://postgres:TWOJE_HASLO_DO_POSTGRES@localhost:5432/portfolio

SECRET_KEY
Value: [Wygeneruj: openssl rand -hex 32]
```

## 🖥️ **KROK 2: Przygotuj EC2 (10 min)**

1. **SSH do twojego EC2:**
```bash
ssh -i twoj-klucz.pem ec2-user@51.20.78.79
```

2. **Sprawdź Security Group** - musi być otwarty port 8000:
   - AWS Console → EC2 → Security Groups
   - Dodaj regułę: Type: Custom TCP, Port: 8000, Source: 0.0.0.0/0

3. **Zainstaluj Docker (jeśli nie masz):**
```bash
sudo yum update -y
sudo yum install docker git -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Zainstaluj Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Restart sesji aby grupa docker zadziałała
exit
ssh -i twoj-klucz.pem ec2-user@51.20.78.79
```

4. **Sprawdź czy PostgreSQL jest zainstalowany i działa:**
```bash
sudo systemctl status postgresql
# Jeśli nie ma PostgreSQL:
sudo yum install postgresql postgresql-server -y
sudo postgresql-setup initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

## 🚀 **KROK 3: Pierwszy deployment (2 min)**

1. **Push zmiany do GitHub** (jeśli jeszcze nie pushowałeś tego co zmienialiśmy)

2. **Uruchom GitHub Action:**
   - Idź do: https://github.com/KGR33N-dev/Portfolio-Backend/actions
   - Kliknij "Deploy Portfolio Backend to AWS EC2"
   - Kliknij "Run workflow" → "Run workflow"

3. **Obserwuj logi** - powinna być zielona ✅ po ~3-5 minutach

## 🌐 **KROK 4: Test API (1 min)**

Sprawdź czy API działa:
```bash
curl http://51.20.78.79:8000/api/health
curl http://51.20.78.79:8000/api/blog/
```

Lub otwórz w przeglądarce:
- http://51.20.78.79:8000/api/health
- http://51.20.78.79:8000/api/blog/

## 💻 **KROK 5: Aktualizuj frontend (Portfolio)**

W swoim projekcie Portfolio (Astro), utwórz/zaktualizuj plik:

**src/config/api.js:**
```javascript
const API_BASE_URL = import.meta.env.MODE === 'development'
  ? 'http://localhost:8000'
  : 'http://51.20.78.79:8000';

export { API_BASE_URL };
```

**Przykład użycia w src/pages/en/blog.astro:**
```javascript
---
import { API_BASE_URL } from '../../config/api.js';

const response = await fetch(`${API_BASE_URL}/api/blog/?language=en`);
const { items: posts } = await response.json();
---

<div>
  {posts.map(post => (
    <article>
      <h2>{post.title}</h2>
      <p>{post.excerpt}</p>
    </article>
  ))}
</div>
```

## 🎯 **Gotowe!**

Po wykonaniu tych kroków:
- ✅ Backend API działa na: http://51.20.78.79:8000
- ✅ Każdy push do main automatycznie wdraża zmiany
- ✅ Frontend może pobierać dane z API
- ✅ Blog posty dostępne przez API

## 🆘 **Troubleshooting**

**GitHub Action fail?**
```bash
# SSH do EC2 i sprawdź logi
ssh -i twoj-klucz.pem ec2-user@51.20.78.79
sudo docker compose -f /opt/portfolio-backend/backend/docker-compose.prod.yml logs
```

**API nie odpowiada?**
- Sprawdź Security Group (port 8000)
- Sprawdź czy kontener działa: `sudo docker ps`

**Frontend nie może połączyć?**
- Sprawdź CORS w przeglądarce (F12 → Console)
- Upewnij się że używasz HTTP nie HTTPS dla API
