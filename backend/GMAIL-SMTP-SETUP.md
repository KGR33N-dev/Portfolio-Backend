# Konfiguracja Gmail SMTP dla Portfolio KGR33N

## 🚀 DARMOWE i NIEZAWODNE rozwiązanie

### 1. Konfiguracja Gmail (jednorazowo):

#### A) Włącz uwierzytelnianie dwuskładnikowe:
- Idź do: https://myaccount.google.com/security
- Włącz "2-Step Verification"

#### B) Utwórz hasło aplikacji:
- Idź do: https://myaccount.google.com/apppasswords
- Wybierz: "Mail" > "Other"
- Nazwa: "Portfolio KGR33N"
- Skopiuj wygenerowane hasło (16 znaków)

### 2. Dodaj do .env:

```bash
 

# Opcjonalne (nadpisują domyślne)
FROM_EMAIL=
FROM_NAME=
ADMIN_EMAIL=
```

### 3. Jak to działa:

✅ **From:** twoj-gmail@gmail.com (wymagane przez Gmail)  
✅ **Reply-To:** noreply@your-domain.com (odpowiedzi idą na Twoją domenę)  
✅ **Limit:** 500 emaili/dzień (wystarczy dla portfolio)  
✅ **Koszt:** 0 zł  
✅ **Niezawodność:** 99.9%  

### 4. Alternatywy (jeśli chcesz więcej):

#### A) Brevo (Sendinblue) - 300 emaili/dzień DARMOWE
```bash
# https://app.brevo.com
BREVO_API_KEY=your-brevo-api-key
```

#### B) Resend - 100 emaili/dzień DARMOWE (ale wymaga weryfikacji domeny)
```bash
# Twoja domena musi być zweryfikowana w dashboard
RESEND_API_KEY=re_your_api_key
```

#### C) Mailgun - 5000 emaili/miesiąc za $35
```bash
MAILGUN_API_KEY=your-mailgun-key
MAILGUN_DOMAIN=mg.kgr33n.com  # subdomena
```

## 🏆 Zalecenie: Gmail SMTP

**Dlaczego Gmail SMTP:**
- ✅ Darmowe
- ✅ Niezawodne 
- ✅ Bez weryfikacji domeny
- ✅ 500 emaili/dzień
- ✅ Gotowe w 5 minut

**Jak Reply-To działa:**
1. Email wysyłany z: `twoj-gmail@gmail.com`
2. Odbiorca widzi: `KGR33N Portfolio <twoj-gmail@gmail.com>`
3. Gdy odpowiada - idzie na: `noreply@your-domain.com`
4. Możesz ustawić przekierowanie noreply@your-domain.com → twój-gmail@gmail.com

## 🔧 Testowanie:

```bash
# Po dodaniu do .env uruchom:
curl -X POST http://localhost:8000/api/test-email
```
