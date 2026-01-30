# Render Deployment Guide - Attendance Bot

This guide provides step-by-step instructions for deploying your Attendance Bot to Render with webhook support for **permanent free hosting**.

## Prerequisites

- [x] GitHub repository with the updated code
- [x] Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- [x] Render account (sign up at [render.com](https://render.com))

## Step 1: Push Your Code to GitHub

Make sure all the updated files are committed and pushed to your GitHub repository:

```bash
git add .
git commit -m "Convert bot to webhook mode for Render deployment"
git push origin main
```

## Step 2: Create a New Web Service on Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **"New +"** button in the top right
3. Select **"Web Service"**
4. Connect your GitHub account if not already connected
5. Select your **Attendance-Bot** repository
6. Click **"Connect"**

## Step 3: Configure the Web Service

Fill in the following settings:

| Setting | Value |
|---------|-------|
| **Name** | `attendance-bot` (or any name you prefer) |
| **Region** | Choose the closest region to you |
| **Branch** | `main` (or your default branch) |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn bot:app` |
| **Instance Type** | **Free** |

## Step 4: Add Environment Variables

In the **Environment Variables** section, click **"Add Environment Variable"** and add:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | Your Telegram bot token from BotFather |

> [!TIP]
> You can also add `BASE_URL` if your college portal URL is different from the default in `config.py`

Click **"Create Web Service"** to start the deployment.

## Step 5: Wait for Deployment

Render will now:
1. Clone your repository
2. Install dependencies from `requirements.txt`
3. Start the Flask app using Gunicorn

Wait for the status to show **"Live"** (usually takes 2-3 minutes).

## Step 6: Activate the Webhook

Once your service is **Live**, you'll see a URL at the top of the page (e.g., `https://attendance-bot-xyz.onrender.com`).

**CRITICAL STEP**: You must tell Telegram to send updates to your webhook URL.

### Option A: Using Your Browser

Open this URL in your browser (replace the placeholders):

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://<YOUR_RENDER_URL>.onrender.com/webhook
```

**Example**:
```
https://api.telegram.org/bot8288985575:AAGuKH42iISvwMRsQkH408oi_bK2UYSOpUI/setWebhook?url=https://attendance-bot-xyz.onrender.com/webhook
```

You should see a JSON response like:
```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

### Option B: Using curl (Command Line)

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://<YOUR_RENDER_URL>.onrender.com/webhook"
```

## Step 7: Test Your Bot

1. Open Telegram and find your bot
2. Send `/start` command
3. You should receive the welcome message
4. Send your credentials: `rollnumber password`
5. Wait for the bot to fetch and display your attendance

> [!NOTE]
> **First Message Delay**: After 15 minutes of inactivity, Render will put your service to sleep. The first message after sleep may take 10-20 seconds to respond as the service wakes up. Subsequent messages will be instant.

## Verification Checklist

- [ ] Service shows "Live" status on Render dashboard
- [ ] Health check endpoint works: Visit `https://your-render-url.onrender.com/` and see "Attendance Bot is Running ✅"
- [ ] Webhook is set: Check the setWebhook URL response shows `"ok": true`
- [ ] Bot responds to `/start` command
- [ ] Bot fetches attendance data correctly
- [ ] Refresh button works
- [ ] `/cancel` command clears sessions

## Troubleshooting

### Bot doesn't respond to messages

**Check webhook status**:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

Look for:
- `url` should be your Render webhook URL
- `has_custom_certificate` should be `false`
- `pending_update_count` should be `0` or low
- Check `last_error_message` for any errors

**Solution**: Re-set the webhook using Step 6

### Service shows "Deploy failed"

**Check Render logs**:
1. Go to your service dashboard
2. Click "Logs" tab
3. Look for error messages

**Common issues**:
- Missing dependencies: Make sure `requirements.txt` is correct
- Syntax errors: Check the logs for Python errors
- Port binding: Render automatically sets the `PORT` environment variable

### Bot responds slowly

This is normal for Render's free tier:
- First message after 15 minutes of inactivity takes 10-20 seconds (cold start)
- Subsequent messages are instant
- This is expected behavior and cannot be avoided on the free tier

### Login fails or attendance not fetched

This is likely a scraping issue, not a deployment issue:
- Verify your credentials are correct
- Check if the college portal is accessible
- Review the Render logs for scraping errors

## Local Testing (Optional)

To test the webhook mode locally before deploying:

1. Set environment variable:
   ```bash
   set USE_POLLING=false
   ```

2. Run the bot:
   ```bash
   python bot.py
   ```

3. Visit `http://localhost:8000/` to see the health check

To test with polling mode (original behavior):
```bash
set USE_POLLING=true
python bot.py
```

## Updating Your Bot

When you make changes to your code:

1. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Your update message"
   git push origin main
   ```

2. Render will automatically detect the changes and redeploy (if auto-deploy is enabled)

3. Or manually deploy from the Render dashboard: Click **"Manual Deploy"** → **"Deploy latest commit"**

## Cost and Limitations

### Free Tier Benefits
- ✅ **Permanent free hosting** (no time limit)
- ✅ **Automatic wake-up** when users send messages
- ✅ **750 hours/month** of runtime (enough for 24/7 with sleep)
- ✅ **Automatic HTTPS** with valid SSL certificate

### Free Tier Limitations
- ⏱️ **Sleeps after 15 minutes** of inactivity
- ⏱️ **10-20 second cold start** for first message after sleep
- 💾 **512 MB RAM** (sufficient for this bot)
- 🔄 **Limited build minutes** (usually not an issue)

## Support

If you encounter issues:
1. Check Render logs for errors
2. Verify webhook is set correctly using `getWebhookInfo`
3. Test the health check endpoint
4. Review the troubleshooting section above

---

**Congratulations!** 🎉 Your Attendance Bot is now running permanently for free on Render!
