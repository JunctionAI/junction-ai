# Unity MMA DM Bot

AI-powered Instagram/Facebook DM bot that handles FAQs, captures leads, and books free trials.

## Quick Start (Demo Mode)

```bash
cd ~/junction-ai/barnaby_dm_bot
pip install -r requirements.txt
python demo_chat.py
```

This lets you test the bot locally without Meta API setup.

## Full Setup (Production)

### 1. Meta Developer Account

1. Go to https://developers.facebook.com/
2. Create an app (Business type)
3. Add "Messenger" and "Instagram" products
4. Get your Page Access Token

### 2. Environment Variables

Add to your `.env`:
```bash
META_ACCESS_TOKEN=your_page_access_token
META_APP_SECRET=your_app_secret
META_VERIFY_TOKEN=unity_mma_2024
```

### 3. Run the Webhook Server

```bash
python meta_webhook.py
```

### 4. Expose with ngrok (for testing)

```bash
ngrok http 5000
```

Copy the HTTPS URL and set it as your webhook in Meta Developer Console.

### 5. Configure Webhook in Meta

1. Go to your app in Meta Developer Console
2. Messenger → Settings → Webhooks
3. Add callback URL: `https://your-ngrok-url/webhook`
4. Verify token: `unity_mma_2024`
5. Subscribe to: `messages`, `messaging_postbacks`

## Leads Dashboard

View captured leads:
```bash
streamlit run leads_dashboard.py
```

## Features

- **FAQ Handling**: Classes, pricing, location, coaches, trial info
- **Lead Capture**: Name, phone, email, experience level, interests
- **AI Responses**: Natural, MMA-friendly conversations using Grok-3
- **Free Trial Push**: Always promotes the 1-Day Free Trial
- **Lead Dashboard**: View and export leads

## Unity MMA Info

- **Location**: 19B William Pickering Drive, Rosedale, Albany, Auckland
- **Phone**: 027 200 7776
- **Email**: Info@unitymma.co.nz
- **Website**: unitymma.co.nz

## Customization

Edit `config.py` to change gym info, pricing, classes, etc.
