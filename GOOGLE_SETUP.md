# Google API Setup for Junction AI

## Gmail & Calendar Integration

### Step 1: Create Google Cloud Project
1. Go to https://console.cloud.google.com/
2. Create a new project called "Junction AI"
3. Enable APIs:
   - Gmail API
   - Google Calendar API

### Step 2: Create OAuth Credentials
1. Go to APIs & Services > Credentials
2. Create OAuth 2.0 Client ID
3. Application type: Desktop App
4. Download the JSON file
5. Rename to `credentials.json` and put in `~/junction-ai/`

### Step 3: Get Refresh Token
Run this once to authenticate:
```bash
cd ~/junction-ai
python3 google_auth.py
```
This opens a browser - sign in with the Gmail account you want to use.
A `token.json` file will be created for future use.

### Step 4: Test
Send these to the bot:
- "Check my inbox"
- "What's on my calendar today?"
- "Send email to john@example.com about the meeting"

## Environment Variables (Optional)
Add to `.env` if you want to specify paths:
```
GOOGLE_CREDENTIALS_PATH=~/junction-ai/credentials.json
GOOGLE_TOKEN_PATH=~/junction-ai/token.json
```

## Scopes Used
- `gmail.readonly` - Read emails
- `gmail.send` - Send emails
- `calendar.readonly` - Read calendar
- `calendar.events` - Create/modify events

## Security Notes
- `credentials.json` contains your OAuth app secrets
- `token.json` contains your access tokens
- Keep both files secure and never commit to git
- Add to `.gitignore`:
  ```
  credentials.json
  token.json
  ```
