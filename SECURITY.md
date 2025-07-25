# 🔒 Security Guidelines

## Environment Variables

### ❌ NEVER commit these files:
- `.env`
- `.env.production`
- `.env.local`
- `.env.development`
- Any file containing real passwords, API keys, or secrets

### ✅ Safe to commit:
- `.env.example` (with placeholder values)
- Configuration templates
- Documentation

## Quick Setup

1. **Copy example file:**
   ```bash
   cp backend/.env.example backend/.env
   ```

2. **Fill in real values:**
   - Replace `password` with your actual database password
   - Generate secret key: `openssl rand -hex 32`
   - Update URLs for your environment

3. **For production deployment:**
   - Use GitHub Secrets for sensitive values
   - Never put real credentials in config files

## GitHub Secrets (Production)

Set these in repository settings → Secrets:

```
EC2_HOST=51.20.78.79
EC2_USER=ec2-user
EC2_SSH_KEY=[full private key content]
DATABASE_URL=postgresql://postgres:REAL_PASSWORD@localhost:5432/portfolio
SECRET_KEY=[generated 32-char hex string]
```

## Database Security

- Use strong passwords (16+ characters)
- Don't use default usernames/passwords in production
- Restrict database access to necessary IPs only
- Regular backups with encryption

## API Security

- CORS configured for specific domains only
- Environment-based configuration
- Health checks don't expose sensitive data
- Proper error handling without leaking info

## File Permissions

```bash
# Secure .env files
chmod 600 .env
chmod 600 .env.production

# Secure SSH keys
chmod 600 *.pem
chmod 600 ~/.ssh/id_rsa
```

Remember: Security is a process, not a one-time setup! 🔐
