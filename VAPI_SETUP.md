# Unity MMA - VAPI Voice Bot Setup

## Get a VAPI Phone Number for Unity MMA

### Step 1: Create VAPI Account

1. Go to https://vapi.ai
2. Sign up / Log in
3. Go to Dashboard → Billing → Add credits ($10 minimum to start)

---

### Step 2: Buy a Phone Number

1. VAPI Dashboard → "Phone Numbers" → "Buy Number"
2. Select:
   - **Country**: New Zealand (+64)
   - **Type**: Local (Auckland if available) or Toll-free
3. Purchase number (~$2-5/month)
4. Note your phone number ID from the dashboard

---

### Step 3: Create the Assistant

1. VAPI Dashboard → "Assistants" → "Create Assistant"
2. Configure:

**Name**: `Unity MMA Receptionist`

**System Prompt**:
```
You are the AI receptionist for Unity MMA, Auckland's newest and most diverse MMA gym located at 19B William Pickering Drive, Rosedale.

Your personality:
- Friendly, warm, and encouraging
- Like a welcoming coach who makes beginners feel comfortable
- Brief and natural - this is a phone call, not an essay

Key information:
- Location: 19B William Pickering Drive, Rosedale, Albany, Auckland
- Phone: 027 200 7776
- Website: unitymma.co.nz

Classes offered:
- MMA (Adults): Tuesday & Thursday 7pm, Friday 6pm
- Kickboxing: Tuesday & Thursday 6pm
- Boxing: Monday 5pm (Beginner), 6pm (Advanced), Sunday 11am
- Jiu Jitsu: Monday 7pm (Gi), Wednesday 7pm (No Gi), Friday 7pm (Open Mat), Saturday 12pm
- Kids/Teens: Multiple classes weekdays 4-5pm, Saturday mornings

Pricing:
- Adults: $49.99/week ($54.99 with BJJ)
- Students: $39.99/week
- Casual: $25/session

ALWAYS offer the FREE 1-Day Trial for new enquiries.

When taking bookings:
1. Get their name
2. Get their phone number
3. Ask what class interests them
4. Confirm the day/time
5. Remind them to arrive 10-15 mins early

If they have personal questions (injuries, experience level, nervous), say Barnaby will call them back personally.

Keep responses SHORT - 2-3 sentences max. This is a phone call.
```

**Voice**: Select a friendly, natural voice (recommend: "nova" or "shimmer")

**First Message**:
```
Hey, thanks for calling Unity MMA! I'm here to help you get started. Are you looking to book a class or just want some info?
```

3. Save the Assistant → Note the Assistant ID

---

### Step 4: Link Phone Number to Assistant

1. VAPI Dashboard → "Phone Numbers"
2. Click your purchased number
3. Set "Assistant" to "Unity MMA Receptionist"
4. Save

---

### Step 5: Add Environment Variables

Add to your `.env` and Render:
```
VAPI_API_KEY=<your-vapi-api-key>
VAPI_PHONE_NUMBER_ID=<your-phone-number-id>
VAPI_ASSISTANT_ID=<your-assistant-id>
```

---

### Step 6: Set Up Call Forwarding

**Option A: Direct VAPI Number**
- Give out the VAPI number directly
- Or add to Google Business Profile

**Option B: Forward Unity MMA's Existing Number**
- Contact Unity MMA's phone provider
- Set up call forwarding to VAPI number when:
  - No answer after X rings
  - Outside business hours
  - Line is busy

---

## Testing

### Test Call
1. Call the VAPI phone number
2. Say: "Hi, I'm interested in trying MMA"
3. Should respond with class info and offer free trial

### Check Logs
1. VAPI Dashboard → "Calls"
2. View transcripts and recordings

---

## Costs

| Item | Cost |
|------|------|
| Phone Number | ~$2-5/month |
| Per minute (inbound) | ~$0.05-0.10/min |
| Per minute (AI processing) | ~$0.10-0.15/min |

**Estimated monthly**: $20-50 depending on call volume

---

## Webhook for Lead Capture (Optional)

To capture leads from calls, deploy the webhook server:

1. Add to Render as a web service:
   - **Start Command**: `gunicorn barnaby_voice_bot.webhook_server:app --bind 0.0.0.0:$PORT`

2. In VAPI Dashboard → Assistant → Webhooks:
   - **Server URL**: `https://unity-voice-webhook.onrender.com/vapi/webhook`

3. Leads will be saved and available at `/leads` endpoint

---

## Quick Reference

| Item | Value |
|------|-------|
| VAPI Dashboard | https://vapi.ai/dashboard |
| Unity MMA Phone | 027 200 7776 |
| VAPI Phone | (Your purchased number) |
| Webhook URL | `https://your-app.onrender.com/vapi/webhook` |
