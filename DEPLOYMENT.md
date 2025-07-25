# Portfolio Backend - AWS EC2 Deployment Guide

## 🚀 Deployment Configuration for kgr33n.com

**Frontend:** https://kgr33n.com (Cloudflare Pages)  
**Backend:** AWS EC2 (eu-north-1) + PostgreSQL  
**Repository:** https://github.com/KGR33N-dev/Portfolio-Backend  

### 📋 Required GitHub Secrets

Go to your repository: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

```
EC2_HOST=51.20.78.79                        # Your EC2 public IP
EC2_USER=ec2-user
EC2_SSH_KEY=YOUR_PRIVATE_SSH_KEY             # Full private key content
DATABASE_URL=postgresql://postgres:YOUR_DB_PASSWORD@localhost:5432/portfolio
SECRET_KEY=YOUR_SECRET_KEY                   # Generate: openssl rand -hex 32
```

### 🏗️ Initial EC2 Setup (One-time)

1. **SSH to your EC2:**
   ```bash
   ssh -i your-key.pem ec2-user@51.20.78.79
   ```

2. **Run setup script:**
   ```bash
   # Download and run EC2 setup
   curl -O https://raw.githubusercontent.com/KGR33N-dev/Portfolio-Backend/main/backend/ec2-setup.sh
   chmod +x ec2-setup.sh
   sudo ./ec2-setup.sh
   ```

3. **Setup PostgreSQL:**
   ```bash
   # Install PostgreSQL
   sudo yum install postgresql postgresql-server -y
   sudo postgresql-setup initdb
   sudo systemctl enable postgresql
   sudo systemctl start postgresql
   
   # Create database and user
   sudo -u postgres psql
   CREATE DATABASE portfolio;
   CREATE USER postgres WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE portfolio TO postgres;
   \q
   ```

4. **Configure PostgreSQL for local access:**
   ```bash
   sudo nano /var/lib/pgsql/data/pg_hba.conf
   # Change local connections to md5
   sudo systemctl restart postgresql
   ```

### 🚀 Deployment Process

1. **Push to main branch** triggers automatic deployment
2. **Or manually trigger** from GitHub Actions tab

The workflow will:
- Connect to your EC2
- Pull latest code
- Build Docker container
- Start FastAPI service
- Verify deployment

### 🌐 Frontend Integration (Astro)

Update your Astro project's API configuration:

```javascript
// src/config/api.js
const API_BASE_URL = import.meta.env.MODE === 'development'
  ? 'http://localhost:8000'
  : 'http://51.20.78.79:8000';

export { API_BASE_URL };
```

Example blog page:
```astro
---
// src/pages/en/blog.astro
import { API_BASE_URL } from '../../config/api.js';

const response = await fetch(`${API_BASE_URL}/api/blog/?language=en`);
const { items: posts } = await response.json();
---

<div>
  {posts.map(post => (
    <article>
      <h2>{post.title}</h2>
      <p>{post.excerpt}</p>
      <a href={`/en/blog/${post.slug}`}>Read more</a>
    </article>
  ))}
</div>
```

### 🏗️ Initial EC2 Setup

1. **Launch EC2 Instance:**
   - AMI: Amazon Linux 2
   - Instance Type: t2.micro (free tier) or t3.small
   - Security Groups: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (API)

2. **Run setup script on EC2:**
   ```bash
   ssh -i your-key.pem ec2-user@your-ec2-ip
   curl -O https://raw.githubusercontent.com/your-username/Portfolio-Backend/main/backend/ec2-setup.sh
   chmod +x ec2-setup.sh
   sudo ./ec2-setup.sh
   ```

3. **Clone repository:**
   ```bash
   cd /opt/portfolio-backend
   git clone https://github.com/your-username/Portfolio-Backend.git .
   ```

### 🗄️ Database Setup (AWS RDS)

1. **Create RDS PostgreSQL instance**
2. **Configure security group** to allow connections from EC2
3. **Get connection string:**
   ```
   postgresql://username:password@your-rds-endpoint.region.rds.amazonaws.com:5432/portfolio
   ```

### 🌐 Domain Configuration (Cloudflare)

1. **Add A record:** `api.your-domain.com` → EC2 IP
2. **Enable Cloudflare proxy** (orange cloud)
3. **SSL/TLS:** Set to "Full (strict)"

### 🔄 Deployment Process

Every push to `main` branch triggers:

1. **GitHub Actions** connects to EC2
2. **Pulls latest code** from repository
3. **Builds Docker containers** with new code
4. **Restarts services** with zero downtime
5. **Verifies deployment** with health check

### 📱 Frontend Integration

Your frontend can call API endpoints:

```javascript
// Production
const API_URL = 'https://api.your-domain.com';

// Development  
const API_URL = 'http://localhost:8000';

// Example usage
fetch(`${API_URL}/api/blog/`)
  .then(response => response.json())
  .then(data => console.log(data));
```

### 🔍 Monitoring & Logs

```bash
# Check container status
sudo docker compose -f backend/docker-compose.prod.yml ps

# View logs
sudo docker compose -f backend/docker-compose.prod.yml logs -f

# Check health
curl http://localhost:8000/api/health
```

### 🛠️ Manual Deployment

If needed, deploy manually:

```bash
cd /opt/portfolio-backend
git pull origin main
sudo docker compose -f backend/docker-compose.prod.yml down
sudo docker compose -f backend/docker-compose.prod.yml up -d --build
```

### 📊 API Endpoints

- `GET /` - Root endpoint
- `GET /api/health` - Health check
- `GET /api/blog/` - List blog posts
- `POST /api/blog/` - Create blog post
- `GET /api/blog/{slug}` - Get blog post by slug
- `PUT /api/blog/{id}` - Update blog post
- `PUT /api/blog/{id}/publish` - Publish blog post

### 🔐 Security Features

- **CORS** configured for your frontend domain
- **Environment variables** for sensitive data
- **Docker containers** for isolation
- **Nginx proxy** (optional) for additional security
- **Health checks** for reliability

### 🚨 Troubleshooting

**Container won't start:**
```bash
sudo docker compose -f backend/docker-compose.prod.yml logs web
```

**Database connection issues:**
- Check DATABASE_URL format
- Verify RDS security groups
- Test connection manually

**CORS errors:**
- Verify PRODUCTION_FRONTEND environment variable
- Check Cloudflare proxy settings

**GitHub Actions failing:**
- Verify all secrets are set correctly
- Check EC2 SSH access
- Review action logs in GitHub
