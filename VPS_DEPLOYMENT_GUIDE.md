# COGNISPACE — VPS Deployment Guide

## System Requirements

| Item | Minimum | Recommended |
|---|---|---|
| **OS** | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| **RAM** | 2 GB | 4 GB |
| **CPU** | 1 vCPU | 2 vCPU |
| **Disk** | 20 GB SSD | 40 GB SSD |
| **Python** | 3.11+ | 3.11 |
| **Node.js** | 18+ | 20.x |
| **MongoDB** | 6.0+ | 7.0+ |

---

## Step 1: VPS Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essentials
sudo apt install -y git curl wget nginx certbot python3-certbot-nginx supervisor

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install yarn
npm install -g yarn

# Install MongoDB 7.0 (ya MongoDB Atlas use karein - recommended)
# Atlas: https://www.mongodb.com/cloud/atlas (Free tier available)
```

---

## Step 2: Code Deploy

```bash
# Clone from GitHub (pehle Emergent se "Save to GitHub" karein)
cd /opt
sudo git clone https://github.com/YOUR_REPO/cognispace.git
cd cognispace
```

---

## Step 3: Backend Setup

```bash
cd /opt/cognispace/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# emergentintegrations ke liye:
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

### Backend `.env` file create karein:

```bash
nano /opt/cognispace/backend/.env
```

```env
MONGO_URL=mongodb+srv://USERNAME:PASSWORD@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=cognispace
CORS_ORIGINS=https://yourdomain.com
JWT_SECRET=GENERATE_A_RANDOM_64_CHAR_STRING_HERE
SUPER_ADMIN_USERNAME=admin
SUPER_ADMIN_PASSWORD=YOUR_SECURE_PASSWORD
FRONTEND_URL=https://yourdomain.com
EMERGENT_LLM_KEY=YOUR_EMERGENT_UNIVERSAL_KEY
ANTHROPIC_API_KEY=YOUR_EMERGENT_UNIVERSAL_KEY
RESEND_API_KEY=YOUR_RESEND_API_KEY
SENDER_EMAIL=noreply@yourdomain.com
TWILIO_ACCOUNT_SID=YOUR_TWILIO_SID
TWILIO_AUTH_TOKEN=YOUR_TWILIO_AUTH_TOKEN
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

### Environment Variables Details:

| Variable | Description | Kahan se milega |
|---|---|---|
| `MONGO_URL` | MongoDB connection string | MongoDB Atlas → Connect → Driver |
| `DB_NAME` | Database name | `cognispace` rakhein |
| `CORS_ORIGINS` | Frontend URL (comma separated) | Aapka domain: `https://yourdomain.com` |
| `JWT_SECRET` | Random secret for auth tokens | `openssl rand -hex 32` se generate karein |
| `SUPER_ADMIN_USERNAME` | Admin login username | Apni choice |
| `SUPER_ADMIN_PASSWORD` | Admin login password | Strong password rakhein |
| `FRONTEND_URL` | Frontend URL for emails/links | `https://yourdomain.com` |
| `EMERGENT_LLM_KEY` | AI features ke liye | Emergent → Profile → Universal Key |
| `ANTHROPIC_API_KEY` | Same as EMERGENT_LLM_KEY | Same key |
| `RESEND_API_KEY` | Email sending ke liye | https://resend.com → API Keys |
| `SENDER_EMAIL` | Emails ka "from" address | Resend mein verified domain ka email |
| `TWILIO_ACCOUNT_SID` | WhatsApp messages ke liye | https://console.twilio.com |
| `TWILIO_AUTH_TOKEN` | WhatsApp auth | Twilio Console → Auth Token |
| `TWILIO_WHATSAPP_FROM` | WhatsApp sender number | Twilio Console → WhatsApp Sandbox |

---

## Step 4: Frontend Setup

```bash
cd /opt/cognispace/frontend

# Install dependencies
yarn install

# Create .env
nano .env
```

```env
REACT_APP_BACKEND_URL=https://yourdomain.com
```

```bash
# Build production bundle
yarn build
```

---

## Step 5: Supervisor (Process Manager)

```bash
sudo nano /etc/supervisor/conf.d/cognispace.conf
```

```ini
[program:cognispace-backend]
directory=/opt/cognispace/backend
command=/opt/cognispace/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/cognispace/backend.err.log
stdout_logfile=/var/log/cognispace/backend.out.log
environment=PATH="/opt/cognispace/backend/venv/bin:%(ENV_PATH)s"
```

```bash
sudo mkdir -p /var/log/cognispace
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start cognispace-backend
```

---

## Step 6: Nginx (Reverse Proxy + SSL)

```bash
sudo nano /etc/nginx/sites-available/cognispace
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend (React build)
    location / {
        root /opt/cognispace/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
        client_max_body_size 10M;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/cognispace /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# SSL Certificate (free via Let's Encrypt)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## Step 7: DNS Setup

Domain provider (GoDaddy/Namecheap/Cloudflare) mein:

| Type | Name | Value |
|---|---|---|
| A | @ | YOUR_VPS_IP |
| A | www | YOUR_VPS_IP |

---

## Step 8: Verify

```bash
# Backend check
curl https://yourdomain.com/api/auth/super-admin/login \
  -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR_PASSWORD"}'

# Frontend check
curl https://yourdomain.com  # Should return HTML
```

---

## Maintenance Commands

```bash
# Logs dekhein
sudo tail -f /var/log/cognispace/backend.err.log

# Backend restart
sudo supervisorctl restart cognispace-backend

# Code update
cd /opt/cognispace && git pull
cd backend && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && yarn install && yarn build
sudo supervisorctl restart cognispace-backend
sudo systemctl restart nginx

# SSL auto-renew (already configured by certbot)
sudo certbot renew --dry-run
```

---

## MongoDB Atlas Setup (Recommended)

1. https://www.mongodb.com/cloud/atlas par jaayein
2. Free Cluster create karein (M0 - Free tier)
3. Database Access → User create karein
4. Network Access → VPS ka IP whitelist karein (ya 0.0.0.0/0 for all)
5. Connect → Drivers → Connection string copy karein
6. Backend `.env` mein `MONGO_URL` mein paste karein

---

## Security Checklist

- [ ] UFW Firewall enable karein: `sudo ufw allow 22,80,443/tcp && sudo ufw enable`
- [ ] SSH key-based login enable karein, password disable
- [ ] MongoDB Atlas mein IP whitelist karein
- [ ] Strong JWT_SECRET use karein (min 64 chars)
- [ ] Strong SUPER_ADMIN_PASSWORD rakhein
- [ ] Regular backups setup karein
- [ ] Fail2ban install karein: `sudo apt install fail2ban`
