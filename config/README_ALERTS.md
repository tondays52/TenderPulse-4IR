# TenderPulse 4IR - Real WhatsApp & SMS Alert Setup Guide

TenderPulse 4IR now includes a unified multi-channel alert dispatcher ([`backend/dispatcher.ps1`](../backend/dispatcher.ps1)) that can send real messages directly to your phone the moment a new tender is discovered.

Configuration file: [`config/alerts_config.json`](./alerts_config.json)

---

## Option 1: Free Direct WhatsApp (Easiest — 30 Seconds Setup)
You can receive formatted WhatsApp messages on your personal phone for free using **CallMeBot**:

1. Add the phone number **`+34 644 68 07 43`** (or **`+34 644 76 66 43`**) to your phone contacts as "CallMeBot".
2. Open WhatsApp and send this exact text message to that number:
   ```
   I allow callmebot to send me messages
   ```
3. CallMeBot will reply immediately with:
   > *"API Activated for your phone number. Your APIKEY is: 123456"*
4. Open [`config/alerts_config.json`](./alerts_config.json) and enter:
   ```json
   "whatsapp_callmebot": {
     "enabled": true,
     "phone": "+88018XXXXXXXX",  // Your WhatsApp phone number with country code
     "apiKey": "123456"          // The API key you received
   }
   ```
5. Run [`backend/test_alert.ps1`](../backend/test_alert.ps1) to test! A real WhatsApp message will arrive on your phone instantly.

---

## Option 2: Twilio WhatsApp & SMS (Enterprise)
If you have a Twilio account:
1. Open [`config/alerts_config.json`](./alerts_config.json)
2. Enable Twilio:
   ```json
   "twilio_whatsapp_sms": {
     "enabled": true,
     "accountSid": "AC...",
     "authToken": "...",
     "fromWhatsApp": "whatsapp:+14155238886",
     "toPhone": "+88018XXXXXXXX"
   }
   ```

---

## Option 3: Local Bangladesh SMS (Greenweb / Alpha SMS)
To send real local SMS to Bangladeshi contractors:
1. Obtain an API token from [Greenweb](https://greenweb.com.bd) or any standard BD SMS gateway.
2. In [`config/alerts_config.json`](./alerts_config.json):
   ```json
   "greenweb_bd_sms": {
     "enabled": true,
     "token": "YOUR_GREENWEB_TOKEN",
     "toPhone": "018XXXXXXXX"
   }
   ```

---

## Option 4: Free Telegram Push Alerts
1. Create a bot with `@BotFather` on Telegram.
2. Put the bot token and your chat ID in [`config/alerts_config.json`](./alerts_config.json).
