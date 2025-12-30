# 🚀 Deployment Guide - Vignan ECAP Attendance Bot

This guide will help you deploy your Telegram bot to the cloud for **24/7 availability** without needing your local machine running.

## 📋 Prerequisites

- Your bot code (already ready!)
- A GitHub account (for easy deployment)
- Your Telegram Bot Token

---

## ✨ Recommended: Deploy to Render (FREE)

**Render** offers a free tier perfect for Telegram bots with automatic deployments from GitHub.

### Step 1: Push Code to GitHub

1. Create a new repository on GitHub
2. Push your code:
```bash
git init
git add .
git commit -m "Initial commit - Vignan Attendance Bot"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Step 2: Deploy to Render

1. **Sign up** at [render.com](https://render.com) (free account)

2. **Create New Web Service**:
   - Click "New +" → "Background Worker"
   - Connect your GitHub repository
   - Select your attendance bot repository

3. **Configure the Service**:
   - **Name**: `vignan-attendance-bot` (or any name you prefer)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Instance Type**: `Free`

4. **Add Environment Variables**:
   - Click "Environment" tab
   - Add variable:
     - **Key**: `BOT_TOKEN`
     - **Value**: `8288985575:AAGuKH42iISvwMRsQkH408oi_bK2UYSOpUI`

5. **Deploy**:
   - Click "Create Background Worker"
   - Wait 2-3 minutes for deployment
   - ✅ Your bot is now live 24/7!

### Step 3: Verify Deployment

1. Check the **Logs** tab on Render to see bot activity
2. Open Telegram and test your bot
3. The bot will respond instantly, even when your computer is off!

---

## 🚂 Alternative: Deploy to Railway (FREE)

**Railway** offers $5 free credit monthly (enough for a small bot).

### Quick Deploy Steps:

1. **Sign up** at [railway.app](https://railway.app)

2. **New Project**:
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

3. **Configure**:
   - Railway auto-detects Python
   - Add environment variable:
     - `BOT_TOKEN` = `8288985575:AAGuKH42iISvwMRsQkH408oi_bK2UYSOpUI`

4. **Deploy**:
   - Click "Deploy"
   - Bot goes live in ~2 minutes!

---

## 🐍 Alternative: PythonAnywhere (FREE)

**PythonAnywhere** is great for Python apps with a generous free tier.

### Deploy Steps:

1. **Sign up** at [pythonanywhere.com](https://www.pythonanywhere.com) (free account)

2. **Upload Code**:
   - Go to "Files" tab
   - Upload your project files or clone from GitHub:
     ```bash
     git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
     ```

3. **Install Dependencies**:
   - Open a Bash console
   - Navigate to your project:
     ```bash
     cd YOUR_REPO
     pip install --user -r requirements.txt
     ```

4. **Set Environment Variable**:
   - Edit `~/.bashrc`:
     ```bash
     echo 'export BOT_TOKEN="8288985575:AAGuKH42iISvwMRsQkH408oi_bK2UYSOpUI"' >> ~/.bashrc
     source ~/.bashrc
     ```

5. **Create Always-On Task**:
   - Go to "Tasks" tab
   - Add a new task: `python3 /home/YOUR_USERNAME/YOUR_REPO/bot.py`
   - Set to run daily (free tier limitation)
   
   **Note**: Free tier tasks restart daily. For true 24/7, consider Render or Railway.

---

## 🔒 Security Best Practices

### For Production Deployment:

1. **Never commit `.env` file**:
   - Create `.gitignore`:
     ```
     .env
     __pycache__/
     *.pyc
     ```

2. **Use Environment Variables**:
   - Your bot is already configured to use `BOT_TOKEN` from environment
   - Set it in your deployment platform's dashboard

3. **Rotate Bot Token** (optional):
   - If token was exposed, regenerate it via @BotFather on Telegram
   - Update environment variable on your deployment platform

---

## 📊 Monitoring Your Bot

### Render:
- **Logs**: Dashboard → Your Service → Logs tab
- **Restart**: Dashboard → Manual Deploy → "Clear build cache & deploy"

### Railway:
- **Logs**: Project → Deployments → View Logs
- **Restart**: Deployments → Redeploy

### PythonAnywhere:
- **Logs**: Files → `/home/YOUR_USERNAME/YOUR_REPO/` → Check error logs
- **Restart**: Tasks → Restart task

---

## 🐛 Troubleshooting

### Bot Not Responding:

1. **Check Logs**:
   - Look for error messages in deployment platform logs
   - Common issues: Missing dependencies, wrong Python version

2. **Verify Environment Variables**:
   - Ensure `BOT_TOKEN` is set correctly
   - No extra spaces or quotes

3. **Test Locally First**:
   ```bash
   python bot.py
   ```
   - If it works locally, deployment should work too

### "Module Not Found" Error:

- Ensure `requirements.txt` is complete
- Rebuild/redeploy to reinstall dependencies

### Bot Stops After Some Time:

- **Free tier limitations**: Some platforms may sleep inactive services
- **Render**: Free tier doesn't sleep background workers ✅
- **Railway**: $5/month credit should be enough
- **PythonAnywhere**: Free tier restarts daily

---

## 🎉 Success!

Once deployed, your bot will:
- ✅ Run 24/7 without your computer
- ✅ Respond instantly to user requests
- ✅ Auto-restart if it crashes
- ✅ Update automatically when you push to GitHub (Render/Railway)

**Test it**: Send a message to your bot on Telegram - it should respond immediately!

---

## 💡 Tips

1. **Auto-Deploy**: Render and Railway auto-deploy when you push to GitHub
2. **Logs**: Always check logs first when troubleshooting
3. **Free Tier**: Render's free tier is perfect for this bot
4. **Scaling**: If you get many users, upgrade to paid tier for better performance

Need help? Check the logs on your deployment platform or test locally first!
