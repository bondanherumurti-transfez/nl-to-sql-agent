# DigitalOcean Deployment Checklist

## ✅ Pre-Deployment (Do This First)

### 1. Set Up Neon Database
- [ ] Sign up at [Neon.tech](https://neon.tech)
- [ ] Create a new project
- [ ] Copy the connection string and extract credentials (Host, User, Password, DB Name)
- [ ] Go to Neon **SQL Editor**
- [ ] Copy content from `samples/generate_sample_data.sql` and run it in the editor
- [ ] Verify tables are created and data is populated in Neon UI

### 2. Test Bot Locally
```bash
# Make sure python-telegram-bot is installed
pip install -r requirements.txt

# Run the bot
python bot_telegram.py
```

Expected output:
```
Telegram bot initialized successfully
Starting Telegram bot...
Bot is running! Press Ctrl+C to stop.
```

- [ ] Bot starts without errors
- [ ] Find your bot in Telegram (search for username you created)
- [ ] Send `/start` - you should get welcome message
- [ ] Try a query: "How many customers do we have?"
- [ ] Verify it works!

### 3. Prepare GitHub Repository

```bash
# Initialize git if not done
git init

# Check status
git status

# Add all files (Dockerfile, bot_telegram.py, etc.)
git add .

# Commit
git commit -m "Add Telegram bot for deployment"

# Create GitHub repo (go to github.com/new)
# Then add remote (replace with your URL):
git remote add origin https://github.com/YOUR-USERNAME/nl-to-sql-agent.git

# Push to GitHub
git push -u origin main
```

- [ ] Code pushed to GitHub
- [ ] Repository is public or you've authorized DigitalOcean

---

## 🚀 DigitalOcean Deployment

### Step 1: Create DigitalOcean Account
- [ ] Go to https://www.digitalocean.com/
- [ ] Sign up (get $200 credit for 60 days!)
- [ ] Verify email

### Step 2: Create New App
1. [ ] Click **"Create"** → **"Apps"**
2. [ ] Select **"GitHub"** as source
3. [ ] Click **"Manage Access"** to authorize DigitalOcean
4. [ ] Select **"Only select repositories"**
5. [ ] Choose your `nl-to-sql-agent` repository
6. [ ] Click **"Install & Authorize"**

### Step 3: Configure Source
1. [ ] **Repository**: Select `your-username/nl-to-sql-agent`
2. [ ] **Branch**: `main`
3. [ ] **Source Directory**: `/` (root)
4. [ ] **Autodeploy**: ✅ Check "Autodeploy code changes"
5. [ ] Click **"Next"**

### Step 4: Configure Resource
1. [ ] **Resource Type**: Should auto-detect as **"Worker"** (not Web Service!)
   - If it says "Web Service", manually change to "Worker"
2. [ ] **Dockerfile Path**: `Dockerfile` (should auto-detect)
3. [ ] **Run Command**: Leave as default (`CMD` from Dockerfile)
4. [ ] Click **"Next"**

### Step 5: Environment Variables (IMPORTANT!)

Click "Edit" next to environment variables and add these:

**Database Configuration:**
```
DB_HOST = your_database_host (Encrypt: ✅)
DB_PORT = 5432 (Encrypt: ❌)
DB_NAME = your_database_name (Encrypt: ✅)
DB_USER = your_db_username (Encrypt: ✅)
DB_PASSWORD = your_db_password (Encrypt: ✅)
```

**API Keys:**
```
ANTHROPIC_API_KEY = your_claude_key (Encrypt: ✅)
TELEGRAM_BOT_TOKEN = your_telegram_token (Encrypt: ✅)
```

**PostgreSQL Connection Options (for Neon):**
```
DB_SSLMODE = require (Encrypt: ❌)
DB_CHANNEL_BINDING = require (Encrypt: ❌)
```

**Optional Settings:**
```
TELEGRAM_ALLOWED_USERS = (leave empty or add user IDs) (Encrypt: ❌)
MAX_RETRIES = 3 (Encrypt: ❌)
QUERY_TIMEOUT = 30 (Encrypt: ❌)
DEFAULT_LIMIT = 100 (Encrypt: ❌)
```

- [ ] All environment variables added
- [ ] Sensitive values encrypted
- [ ] Click **"Save"**

### Step 6: Choose Plan
1. [ ] **App Name**: `nl-to-sql-bot` (or your choice)
2. [ ] **Region**: Choose closest to you (e.g., New York, San Francisco, London)
3. [ ] **Plan**: **Basic**
4. [ ] **Instance Size**: **Basic XXS** ($5/month)
   - 512 MB RAM
   - 0.5 vCPU
   - Enough for moderate traffic
5. [ ] Review cost: ~$5/month
6. [ ] Click **"Next"**

### Step 7: Review and Launch
1. [ ] Review all settings
2. [ ] Click **"Create Resources"**
3. [ ] Wait for deployment (2-5 minutes)

---

## 📊 Monitor Deployment

### Watch Build Logs
1. [ ] Click on your worker component
2. [ ] Go to **"Logs"** tab
3. [ ] Select **"Build"** logs
4. [ ] Should see:
   ```
   Building Dockerfile...
   Step 1/8 : FROM python:3.11-slim
   ...
   Successfully built!
   Starting deployment...
   ```

### Check Runtime Logs
1. [ ] Switch to **"Runtime"** logs
2. [ ] Should see:
   ```
   Telegram bot initialized successfully
   Starting Telegram bot...
   Bot is running!
   ```
3. [ ] If you see errors, check environment variables

---

## ✅ Verify Deployment

### Test Your Bot
1. [ ] Open Telegram
2. [ ] Find your bot (search for username)
3. [ ] Send `/start`
4. [ ] Should get welcome message
5. [ ] Try a query: "How many customers do we have?"
6. [ ] Check that SQL is generated and results returned

### Common Issues

**Bot offline?**
- Check runtime logs for errors
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Make sure all environment variables are set

**"Access denied" in Telegram?**
- Check if `TELEGRAM_ALLOWED_USERS` is set.
- **IMPORTANT**: This must be your numerical **Telegram User ID**, not your username or phone number.
- To find your ID: Message [@userinfobot](https://t.me/userinfobot) on Telegram.
- Add this ID to your environment variables and redeploy.

**Database connection failed?**
- Verify database is accessible from internet
- Check DB credentials in environment variables
- Test connection from DigitalOcean's IP range

**Queries failing?**
- Verify `ANTHROPIC_API_KEY` is valid
- Check runtime logs for specific error
- Ensure database schema is accessible

---

## 🎯 Success Criteria

- [x] Bot responds to `/start` command
- [x] Bot processes natural language queries
- [x] SQL is generated correctly
- [x] Results are returned and formatted
- [x] No errors in runtime logs

---

## 🔄 Making Updates

After initial deployment, to update your bot:

1. Make changes to code locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update bot"
   git push
   ```
3. DigitalOcean automatically rebuilds and deploys!

---

## 📞 Need Help?

- **Deployment Guide**: `docs/DIGITALOCEAN_DEPLOYMENT.md`
- **Bot Documentation**: `docs/BOT_TELEGRAM_DOCS.md`
- **DigitalOcean Support**: https://www.digitalocean.com/support

---

## 💰 Cost Tracking

- Worker: $5/month (Basic XXS)
- Claude API: ~$10-50/month (varies by usage)
- Database: $0 (if using existing)

**Total**: ~$15-55/month

---

Ready to deploy? Start with Step 1 above! 🚀
