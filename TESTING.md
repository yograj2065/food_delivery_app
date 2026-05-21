# OTP Authentication System — Testing Guide

## Prerequisites

```bash
# 1. Install backend dependencies
cd food-ordering-system/backend
pip3 install -r requirements.txt --break-system-packages

# 2. Apply migrations
python3 manage.py migrate

# 3. Start Django server
python3 manage.py runserver

# 4. Start React frontend (separate terminal)
cd food-ordering-system/frontend
npm start
```

---

## SECTION 1 — Manual Testing (Browser)

### Registration Flow

1. Open http://localhost:3000/register
2. Fill in:
   - Username: `testuser`
   - Email: `your-real-email@gmail.com`
   - Password: `password123`
3. Click **Create Account →**
4. You should see the OTP step with 6 input boxes
5. Check your email inbox for a message with subject "🔐 Verify Your Account — OTP Inside"
6. Enter the 6-digit OTP (one digit per box — focus auto-advances)
7. Click **✓ Verify & Activate Account**
8. You should be redirected to `/` and the Navbar should show your username

### Login Flow

1. Open http://localhost:3000/login (or logout first)
2. Enter your username and password
3. Click **Sign In →**
4. Check your email for subject "🔑 Your Login OTP"
5. Enter the OTP
6. Click **✓ Verify & Login**
7. You should be redirected home and logged in

### Logout

1. Click **Logout** in the Navbar
2. Token is deleted from the database
3. You are redirected to `/login`

---

## SECTION 2 — Postman API Testing

### Base URL
```
http://127.0.0.1:8000/api/
```

---

### 2.1 — Register (Step 1)

```
POST /api/register/
Content-Type: application/json

{
  "username": "testuser",
  "email": "your@email.com",
  "password": "password123"
}
```

**Expected 201 response:**
```json
{
  "message": "Registration initiated. Please check your email for the OTP.",
  "email": "your@email.com"
}
```

---

### 2.2 — Verify Registration OTP (Step 2)

```
POST /api/verify-register/
Content-Type: application/json

{
  "email": "your@email.com",
  "otp": "482910"
}
```

**Expected 200 response:**
```json
{
  "message": "Account verified successfully. Welcome!",
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "username": "testuser"
}
```

---

### 2.3 — Login Step 1 (Send OTP)

```
POST /api/login/
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}
```

**Expected 200 response:**
```json
{
  "message": "OTP sent to te****@gmail.com. Please check your email.",
  "email": "your@email.com"
}
```

---

### 2.4 — Login Step 2 (Verify OTP → Token)

```
POST /api/login/verify/
Content-Type: application/json

{
  "email": "your@email.com",
  "otp": "739201"
}
```

**Expected 200 response:**
```json
{
  "message": "Login successful.",
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "username": "testuser"
}
```

---

### 2.5 — Logout

```
POST /api/logout/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Expected 200 response:**
```json
{
  "message": "Logged out successfully."
}
```

---

### 2.6 — Resend OTP

```
POST /api/resend-otp/
Content-Type: application/json

{
  "email": "your@email.com",
  "purpose": "login"
}
```

**Expected 200 response:**
```json
{
  "message": "New OTP sent to te****@gmail.com."
}
```

---

### 2.7 — Authenticated Request (Cart)

```
GET /api/cart/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Expected 200 response:**
```json
{
  "cart": []
}
```

---

## SECTION 3 — Security Behaviour Tests

### OTP Expiry (5 minutes)
1. Request an OTP
2. Wait 6 minutes without entering it
3. Try to verify → should get: `"OTP has expired. Please request a new one."`

### Max Attempts (5 tries)
1. Request an OTP
2. Submit wrong OTP 5 times
3. On the 5th wrong attempt → `"Too many failed attempts. Please request a new OTP."`
4. The OTP record is deleted — must request a new one

### OTP Reuse Prevention
1. Successfully verify an OTP
2. Try to use the same OTP again → `"No active OTP found. Please request a new one."`

### Only Latest OTP is Valid
1. Request OTP → get code A
2. Request OTP again (resend) → get code B
3. Try to use code A → fails (it was deleted when code B was generated)
4. Use code B → succeeds

---

## SECTION 4 — Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `SMTPAuthenticationError` | Wrong Gmail App Password | Generate a new App Password at Google Account → Security → App Passwords. Use the 16-char code WITHOUT spaces in `.env` |
| `SMTPServerDisconnected` | EMAIL_HOST is wrong | Ensure `EMAIL_HOST=smtp.gmail.com` in settings.py (it's hardcoded, not from .env) |
| `No module named 'dotenv'` | python-dotenv not installed | `pip3 install python-dotenv --break-system-packages` |
| `relation "api_emailotp" does not exist` | Migration not applied | `python3 manage.py migrate` |
| `Invalid credentials` on login | User not activated | Complete OTP verification first, or check `is_active=True` in Django admin |
| `Authentication required` on cart | Token not sent | Ensure `Authorization: Token <key>` header is present |
| `CORS error` in browser | Frontend port not in CORS_ALLOWED_ORIGINS | Add your port (e.g. 3001) to `CORS_ALLOWED_ORIGINS` in settings.py |
| OTP email goes to spam | Gmail treating automated mail as spam | Check spam folder; mark as "Not spam"; use a verified sender domain in production |

---

## SECTION 5 — Cleanup Command

```bash
# Preview what would be deleted (dry run)
python3 manage.py cleanup_otps --dry-run

# Actually delete expired and verified OTPs
python3 manage.py cleanup_otps

# Schedule with cron (every 15 minutes)
*/15 * * * * cd /path/to/backend && python3 manage.py cleanup_otps
```

---

## SECTION 6 — Django Admin

Visit: http://127.0.0.1:8000/admin/

Create a superuser first:
```bash
python3 manage.py createsuperuser
```

In the admin panel you can:
- View all `EmailOTP` records with expiry status
- Manually delete stale OTPs
- Activate/deactivate user accounts
- View all auth tokens
