# Cloudflare DNS Configuration Guide

## DNS Records to Add:

### A Record:
- Type: A
- Name: api
- Content: 13.48.70.51 (your EC2 IP)
- Proxy status: ✅ Proxied (orange cloud)
- TTL: Auto

### CNAME Records (optional backup):
- Type: CNAME  
- Name: backend
- Content: api.kgr33n.com
- Proxy status: ✅ Proxied

## Cloudflare Settings:

### SSL/TLS:
- Encryption mode: Full (strict)
- Edge Certificates: Universal SSL enabled
- Always Use HTTPS: On

### Security:
- Security Level: Medium
- Challenge Passage: 1 hour
- Browser Integrity Check: On
- Privacy Pass: On

### Speed:
- Auto Minify: CSS, JavaScript, HTML
- Brotli: On
- Early Hints: On

### Caching:
- Caching Level: Standard
- Browser Cache TTL: 4 hours
- Development Mode: Off (turn on during development)

### Page Rules (if needed):
1. api.kgr33n.com/api/auth/*
   - Security Level: High
   - Cache Level: Bypass

2. api.kgr33n.com/health
   - Cache Level: Bypass
   - Browser Cache TTL: 30 minutes

### Firewall Rules:
1. Block non-API paths:
   - Expression: (http.request.uri.path ne "/health" and http.request.uri.path ne "/cors-test" and not starts_with(http.request.uri.path, "/api/"))
   - Action: Block

2. Rate limit API:
   - Expression: starts_with(http.request.uri.path, "/api/")
   - Action: Challenge
   - Rate: 100 requests per 10 minutes

3. Strict auth protection:
   - Expression: starts_with(http.request.uri.path, "/api/auth/")
   - Action: JS Challenge
   - Rate: 20 requests per 10 minutes

## Testing Commands:

# Test health endpoint
curl https://api.kgr33n.com/health

# Test CORS
curl -H "Origin: https://kgr33n.com" https://api.kgr33n.com/cors-test

# Test API access
curl -H "Origin: https://kgr33n.com" https://api.kgr33n.com/api/languages
