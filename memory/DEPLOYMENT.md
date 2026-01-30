# COGNISPACE - Deployment Checklist & Guide

**Last Updated**: January 26, 2026  
**Python Version**: 3.11.x (Recommended)

---

## 📋 Pre-Deployment Checklist

### 1. Environment Variables

#### Backend (`/app/backend/.env`)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `MONGO_URL` | ✅ Yes | MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net` |
| `DB_NAME` | ✅ Yes | Database name | `cognispace_prod` |
| `JWT_SECRET` | ✅ Yes | Secret key for JWT tokens (min 32 chars) | `your-super-secret-key-min-32-characters` |
| `CORS_ORIGINS` | ✅ Yes | Allowed origins (comma-separated or `*`) | `https://yourdomain.com` |
| `SUPER_ADMIN_USERNAME` | ✅ Yes | Super admin login username | `admin` |
| `SUPER_ADMIN_PASSWORD` | ✅ Yes | Super admin password (change in prod!) | `StrongP@ssw0rd!` |
| `EMERGENT_LLM_KEY` | ⚠️ AI Features | Emergent LLM API key for AI features | `sk-emergent-xxxxx` |
| `RESEND_API_KEY` | ⚠️ Email | Resend API key for email notifications | `re_xxxxx` |
| `SENDER_EMAIL` | ⚠️ Email | Verified sender email address | `noreply@yourdomain.com` |
| `TWILIO_ACCOUNT_SID` | ⚠️ WhatsApp | Twilio Account SID | `ACxxxxx` |
| `TWILIO_AUTH_TOKEN` | ⚠️ WhatsApp | Twilio Auth Token | `xxxxx` |
| `TWILIO_WHATSAPP_FROM` | ⚠️ WhatsApp | Twilio WhatsApp number | `+14155238886` |

#### Frontend (`/app/frontend/.env`)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `REACT_APP_BACKEND_URL` | ✅ Yes | Backend API base URL (no trailing slash) | `https://api.yourdomain.com` |

---

### 2. Security Checklist

- [ ] **JWT_SECRET**: Changed from default (min 32 random characters)
- [ ] **SUPER_ADMIN_PASSWORD**: Changed from `admin123`
- [ ] **CORS_ORIGINS**: Set to specific domain(s), not `*`
- [ ] **MongoDB**: Using authentication, not localhost
- [ ] **HTTPS**: SSL certificate configured
- [ ] **Environment files**: Not committed to git

---

### 3. Dependencies Check

```bash
# Backend - Install exact versions
cd /app/backend
pip install -r requirements.txt

# Frontend - Install dependencies
cd /app/frontend
yarn install
```

---

## 🔧 Critical Dependencies (Pinned Versions)

### Backend Core
```
fastapi==0.110.1
uvicorn==0.25.0
motor==3.3.1
pymongo==4.5.0
pydantic==2.12.5
python-jose==3.5.0
passlib==1.7.4
bcrypt==4.1.3
```

### AI & Integrations
```
emergentintegrations==0.1.0
openai==1.99.9
resend==2.21.0
twilio==9.10.0
```

### Scheduler
```
APScheduler==3.11.2
```

### Frontend Core
```json
{
  "react": "^18.3.1",
  "react-dom": "^18.3.1",
  "axios": "^1.7.9",
  "tailwindcss": "^3.4.17"
}
```

---

## 🚀 Deployment Steps

### Step 1: Clone & Setup
```bash
git clone <repository>
cd cognispace
```

### Step 2: Backend Setup
```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with production values
```

### Step 3: Frontend Setup
```bash
cd frontend

# Install dependencies
yarn install

# Create .env file
cp .env.example .env
# Set REACT_APP_BACKEND_URL

# Build for production
yarn build
```

### Step 4: Database Setup
```bash
# Ensure MongoDB is running and accessible
# No migrations needed - MongoDB creates collections automatically
```

### Step 5: Start Services

#### Development
```bash
# Backend
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend
yarn start
```

#### Production (with supervisor)
```bash
# Backend
sudo supervisorctl start backend

# Frontend (serve build folder)
sudo supervisorctl start frontend
```

---

## ✅ Post-Deployment Verification

### 1. Health Checks
```bash
# Backend API
curl https://your-api-domain.com/api/health

# Frontend
curl https://your-frontend-domain.com
```

### 2. Login Test
```bash
# Test admin login
curl -X POST https://your-api-domain.com/api/auth/admin-login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'

# Test therapist login
curl -X POST https://your-api-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"therapist-mobile","password":"password"}'
```

### 3. Feature Verification Checklist

| Feature | Test Method | Expected Result |
|---------|-------------|-----------------|
| Login | POST /api/auth/login | Returns JWT token |
| Client List | GET /api/clients | Returns client array |
| AI Features | POST /api/ai/suggest-assessments | Returns suggestions |
| Email | Create client | Receives welcome email |
| WhatsApp | Book appointment (if opted-in) | Receives confirmation |

---

## 🔥 Common Deployment Issues

### Issue 1: MongoDB Connection Failed
```
Error: MongoServerSelectionError
```
**Solution**: 
- Check `MONGO_URL` format
- Verify network access (whitelist IP)
- Ensure auth credentials are correct

### Issue 2: CORS Error
```
Access-Control-Allow-Origin error
```
**Solution**:
- Set `CORS_ORIGINS` to exact frontend URL
- No trailing slash in URLs

### Issue 3: JWT Token Invalid
```
Error: Could not validate credentials
```
**Solution**:
- Ensure same `JWT_SECRET` on all backend instances
- Token might be expired (default 30 days)

### Issue 4: AI Features Not Working
```
Error: Invalid API key
```
**Solution**:
- Verify `EMERGENT_LLM_KEY` is valid
- Check key has sufficient balance

### Issue 5: Email Not Sending
```
Error: Resend API error
```
**Solution**:
- Verify `RESEND_API_KEY`
- Check `SENDER_EMAIL` is verified in Resend dashboard
- Check domain DNS records

---

## 📁 Environment File Templates

### Backend `.env.example`
```env
# Database (REQUIRED)
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net
DB_NAME=cognispace

# Authentication (REQUIRED - CHANGE IN PRODUCTION!)
JWT_SECRET=change-this-to-a-secure-random-string-min-32-chars
SUPER_ADMIN_USERNAME=admin
SUPER_ADMIN_PASSWORD=change-this-strong-password

# CORS (REQUIRED)
CORS_ORIGINS=https://your-frontend-domain.com

# AI Features (Optional - needed for TheraGenie/CogniVision)
EMERGENT_LLM_KEY=sk-emergent-xxxxx

# Email Notifications (Optional)
RESEND_API_KEY=re_xxxxx
SENDER_EMAIL=noreply@yourdomain.com

# WhatsApp Notifications (Optional)
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_WHATSAPP_FROM=+1234567890
```

### Frontend `.env.example`
```env
# Backend API URL (REQUIRED - no trailing slash)
REACT_APP_BACKEND_URL=https://api.yourdomain.com
```

---

## 📊 Monitoring & Logs

### Log Locations (Supervisor)
```bash
# Backend logs
tail -f /var/log/supervisor/backend.out.log
tail -f /var/log/supervisor/backend.err.log

# Frontend logs
tail -f /var/log/supervisor/frontend.out.log
tail -f /var/log/supervisor/frontend.err.log
```

### Key Metrics to Monitor
- API response times
- MongoDB connection pool
- Memory usage
- Scheduler job execution
- Email/WhatsApp delivery rates

---

## 🔄 Rollback Procedure

1. **Stop services**
   ```bash
   sudo supervisorctl stop backend frontend
   ```

2. **Restore previous version**
   ```bash
   git checkout <previous-commit>
   ```

3. **Reinstall dependencies**
   ```bash
   pip install -r requirements.txt
   yarn install
   ```

4. **Restart services**
   ```bash
   sudo supervisorctl start backend frontend
   ```

---

## 📞 Support Contacts

- **Technical Issues**: Check `/app/memory/HANDOVER.md`
- **API Documentation**: `/api/docs` (Swagger UI)
- **Known Issues**: `/app/memory/ROADMAP.md`

---

**Document Version**: 1.0  
**Created**: January 26, 2026
