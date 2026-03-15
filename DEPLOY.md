# Unity MMA AI Systems - Render.com Deployment Guide

## Quick Start (5 minutes)

### Step 1: Create Render Account
1. Go to https://render.com
2. Click "Get Started" → Sign up with GitHub
3. Authorize Render to access your GitHub

### Step 2: Create GitHub Repository
```bash
cd ~/junction-ai
git init
git add .
git commit -m "Unity MMA AI Systems - Initial commit"
gh repo create junction-ai --private --push
```

### Step 3: Deploy on Render

#### Option A: Deploy Both Bots Together (Recommended)
1. Go to Render Dashboard → "New" → "Background Worker"
2. Connect your GitHub repo
3. Configure:
   - **Name**: `unity-mma-bots`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python cloud_runner.py`

#### Option B: Deploy Bots Separately
1. Use "New" → "Blueprint" and select your repo
2. Render will auto-detect `render.yaml` and create both workers

### Step 4: Add Environment Variables
In Render Dashboard, add these secrets for each service:

**Email Bot:**
```
EMAIL_HOST=mail.freeparking.co.nz
IMAP_PORT=993
SMTP_PORT=465
EMAIL_USER=info@unitymma.co.nz
EMAIL_PASSWORD=Social@19B
XAI_API_KEY=<your-xai-key>
```

**Telegram Bot:**
```
TELEGRAM_BOT_TOKEN=<your-telegram-token>
ALLOWED_USER_IDS=<your-telegram-id>
XAI_API_KEY=<your-xai-key>
```

### Step 5: Deploy
Click "Create Background Worker" → Render will build and deploy automatically.

---

## Monitoring

### View Logs
1. Go to your service in Render Dashboard
2. Click "Logs" tab
3. See real-time output from email/telegram bots

### Health Checks
The email bot prints heartbeat every 2.5 minutes:
```
[14:30:00] Waiting... (processed: 5, replied: 3, escalated: 2)
```

### Restart Service
If needed, click "Manual Deploy" → "Deploy latest commit"

---

## Costs

**Render Free Tier:**
- Background workers: $0 (with limitations)
- May spin down after inactivity

**Render Starter ($7/month per service):**
- Always-on background workers
- Recommended for production

**Total for 24/7 operation:**
- Email Bot: $7/month
- Telegram Bot: $7/month
- **Combined runner: $7/month** (best value!)

---

## Troubleshooting

### Email Bot Not Sending
Check SMTP credentials in environment variables. Logs will show:
```
[SMTP] Connected to mail.freeparking.co.nz:465
```

### Telegram Bot Not Responding
Check TELEGRAM_BOT_TOKEN is correct. Test with:
```
curl https://api.telegram.org/bot<TOKEN>/getMe
```

### Service Keeps Restarting
Check logs for Python errors. Common issues:
- Missing environment variables
- Import errors (check requirements.txt)

---

## Files Reference

```
junction-ai/
├── cloud_runner.py      # Combined runner (runs both bots)
├── render.yaml          # Render.com service definitions
├── Procfile             # Process definitions
├── requirements.txt     # Python dependencies
├── .env.example         # Template for environment variables
├── barnaby_email_bot/
│   ├── run_live.py      # Email bot entry point
│   ├── email_handler.py # Email processing logic
│   └── config.py        # Templates and settings
└── telegram_bot/
    └── telegram_bot.py  # Telegram bot entry point
```

---

## Support

Need help? Contact Tom at Junction AI.
