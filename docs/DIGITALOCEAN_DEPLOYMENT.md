# DigitalOcean Deployment Guide

This guide walks you through deploying your NL-to-SQL Telegram bot to DigitalOcean App Platform.

## Prerequisites

- ✅ Telegram bot created and tested locally
- ✅ GitHub account
- ✅ DigitalOcean account ([Sign up here](https://www.digitalocean.com/))
- ✅ Code pushed to a GitHub repository
- ✅ Database accessible from the internet (or DigitalOcean VPC)

## Cost Estimate

- **App Platform (Worker)**: $5/month (basic-xxs tier)
- **Database**: $0 if using existing, $15+/month for managed PostgreSQL
- **Total**: ~$5-20/month

**Free Trial**: DigitalOcean offers $200 credit for new users (60 days)

## Step 1: Prepare Your Repository

### 1.1 Push Code to GitHub

```bash
cd /Users/bondanherumurti/Documents/Projects/nl-to-sql-agent

# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Add Telegram bot deployment files"

# Add GitHub remote (replace with your repo URL)
git remote add origin https://github.com/your-username/nl-to-sql-agent.git

# Push to main branch
git push -u origin main
```

### 1.2 Verify Required Files

Make sure these files are in your repository:
- ✅ `bot_telegram.py` - Telegram bot code
- ✅ `agent.py` - NL-to-SQL agent
- ✅ `requirements.txt` - Python dependencies
- ✅ `Dockerfile` - Container configuration
- ✅ `.dockerignore` - Files to exclude from container
- ✅ `.do/app.yaml` - DigitalOcean configuration (optional but recommended)

### 1.3 Update .do/app.yaml

Edit `.do/app.yaml` and replace `your-username/nl-to-sql-agent` with your actual GitHub repository:

```yaml
services:
  - name: telegram-bot
    github:
      repo: YOUR-GITHUB-USERNAME/nl-to-sql-agent  # ← Change this
      branch: main
```

## Step 2: Create DigitalOcean App

### 2.1 Access DigitalOcean Dashboard

1. Log in to [DigitalOcean](https://cloud.digitalocean.com/)
2. Click "Create" → "App Platform"

### 2.2 Connect GitHub

1. Click "GitHub" as your source
2. Click "Manage Access" to authorize DigitalOcean
3. Select "Only select repositories"
4. Choose your `nl-to-sql-agent` repository
5. Click "Install & Authorize"

### 2.3 Configure Source

1. **Repository**: Select `your-username/nl-to-sql-agent`
2. **Branch**: `main`
3. **Source Directory**: `/` (root)
4. **Autodeploy**: ✅ Enable (redeploy on git push)

Click "Next"

## Step 3: Configure App

### 3.1 Resource Type

DigitalOcean should auto-detect your `Dockerfile`:

- **Resource Type**: Worker (not Web Service)
- **Dockerfile Path**: `Dockerfile`

> **Note**: Choose "Worker" not "Web Service" because the bot doesn't serve HTTP requests

### 3.2 Instance Size

- **Plan**: Basic
- **Instance Size**: Basic XXS ($5/month)
  - 512 MB RAM / 0.5 vCPU
  - Sufficient for low-to-medium traffic

Click "Next"

## Step 4: Environment Variables

Add the following environment variables as **encrypted** values:

### 4.1 Database Configuration

| Key | Value | Type | Example |
|-----|-------|------|---------|
| `DB_HOST` | Your database host | Encrypted | `db.example.com` |
| `DB_PORT` | Database port | Plain | `5432` |
| `DB_NAME` | Database name | Encrypted | `analytics_db` |
| `DB_USER` | Database username | Encrypted | `bot_user` |
| `DB_PASSWORD` | Database password | Encrypted | `your_password` |

### 4.2 API Keys

| Key | Value | Type |
|-----|-------|------|
| `ANTHROPIC_API_KEY` | Your Claude API key | Encrypted |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Encrypted |

### 4.3 Bot Configuration

| Key | Value | Type | Default |
|-----|-------|------|---------|
| `TELEGRAM_ALLOWED_USERS` | User IDs (optional) | Plain | `` |
| `MAX_RETRIES` | Max SQL retry attempts | Plain | `3` |
| `QUERY_TIMEOUT` | Query timeout (seconds) | Plain | `30` |
| `DEFAULT_LIMIT` | Default result limit | Plain | `100` |

### 4.4 How to Add Variables

1. Click "Edit" next to environment variables
2. Click "Add Variable"
3. Enter Key and Value
4. Select "Encrypt" for sensitive values
5. Click "Save"

Repeat for all variables above.

## Step 5: Review and Launch

### 5.1 Review Configuration

- **App Name**: `nl-to-sql-bot` (or your choice)
- **Region**: Choose closest to your users (e.g., `NYC`, `SFO`, `LON`)
- **Resources**: 1 Worker
- **Estimated Cost**: $5/month

### 5.2 Launch App

1. Click "Create Resources"
2. Wait for deployment (2-5 minutes)

### 5.3 Monitor Deployment

Watch the build logs:
1. Click on your worker component
2. Go to "Logs" tab  
3. Select "Build" logs

You should see:
```
Building Dockerfile...
Step 1/8 : FROM python:3.11-slim
...
Successfully built!
Starting deployment...
```

## Step 6: Verify Deployment

### 6.1 Check Runtime Logs

1. Switch to "Runtime" logs
2. You should see:
   ```
   Telegram bot initialized successfully
   Starting Telegram bot...
   Bot is running! Press Ctrl+C to stop.
   ```

### 6.2 Test Bot in Telegram

1. Open Telegram
2. Find your bot
3. Send `/start`
4. You should get the welcome message
5. Try a query: "How many customers do we have?"

### 6.3 Troubleshooting

**Bot offline?**
- Check runtime logs for errors
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Ensure all environment variables are set

**Database connection failed?**
- Verify database is accessible from internet
- Check `DB_HOST`, `DB_USER`, `DB_PASSWORD`
- Test connection from DigitalOcean's IP range

**Queries failing?**
- Check `ANTHROPIC_API_KEY` is valid
- Review runtime logs for specific errors
- Ensure database schema is accessible

## Step 7: Configure Auto-Deploy

Auto-deploy is already enabled if you checked the box during setup.

**To manually trigger deployment:**
1. Make changes to your code
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update bot"
   git push
   ```
3. DigitalOcean automatically rebuilds and deploys

**Monitor deployments:**
- Go to "Deployments" tab
- See history of all deployments
- Rollback if needed

## Step 8: Database Connectivity

### Option A: Public Database

If your database has a public IP:
1. Whitelist DigitalOcean IP ranges
2. Use SSL/TLS connection (recommended)
3. Update connection string in environment variables

### Option B: DigitalOcean Managed Database

If using DO managed PostgreSQL:
1. Create database in same region as app
2. Enable "Trusted Sources" → Add your app
3. Use private VPC connection (faster, more secure)
4. Get connection details from database dashboard

### Option D: Neon Serverless PostgreSQL (Recommended)

1. Sign up at [Neon.tech](https://neon.tech).
2. Create a new project (e.g., `nl-to-sql-agent-db`).
3. Select the latest PostgreSQL version.
4. In the Dashboard, find your **Connection String**. It will look like:
   `postgresql://alex:AbC123dEf@ep-cool-darkness-123456.us-east-2.aws.neon.tech/neondb?sslmode=require`
5. Extract the credentials for your DigitalOcean Environment Variables:
   - **DB_HOST**: `ep-cool-darkness-123456.us-east-2.aws.neon.tech`
   - **DB_USER**: `alex`
   - **DB_PASSWORD**: `AbC123dEf`
   - **DB_NAME**: `neondb`
   - **DB_PORT**: `5432`

### Step 9: Initialize Schema and Data (Neon)

To set up your database tables and populate them with sample data:

1. In the Neon Console, go to the **SQL Editor** tab.
2. Open the file [generate_sample_data.sql](file:///Users/bondanherumurti/Documents/Projects/nl-to-sql-agent/samples/generate_sample_data.sql).
3. Copy the entire content of the SQL file.
4. Paste it into the Neon SQL Editor.
5. Click **Run**.
6. Verify tables are created in the **Tables** tab.

## Advanced Configuration

### Custom Domain (Optional)

While bots don't need domains, if you add a web dashboard later:

1. Go to "Settings" → "Domains"
2. Add your domain
3. Configure DNS records as shown
4. Enable HTTPS (automatic with Let's Encrypt)

### Scaling

To handle more traffic:

1. **Vertical Scaling**: Upgrade instance size
   - Basic XXS → Basic XS ($12/month)
   - More RAM, faster responses

2. **Horizontal Scaling**: Add more instances
   - Not needed for Telegram bots (single instance is fine)

### Monitoring

1. **Built-in Metrics**:
   - Go to "Insights" tab
   - View CPU, Memory, Bandwidth

2. **Alerts**:
   - Create alerts for high CPU, memory, or crashes
   - Notifications via email

3. **Log Management**:
   - Export logs to external service (Papertrail, Logtail)
   - Set up in "Settings" → "Logging"

### Environment Management

**Development vs Production:**

Create separate apps for dev and prod:
- `nl-to-sql-bot-dev` (points to `develop` branch)
- `nl-to-sql-bot-prod` (points to `main` branch)

Different environment variables for each.

## Maintenance

### View Logs

```bash
# Or use DigitalOcean CLI (doctl)
doctl apps logs YOUR_APP_ID --type run
```

### Restart App

If bot becomes unresponsive:
1. Go to "Settings"
2. Click "Force Rebuild and Deploy"

### Update Dependencies

1. Edit `requirements.txt`
2. Commit and push
3. Auto-deploy rebuilds with new dependencies

### Database Migrations

If you change database schema:
1. Run migrations on database first
2. Then deploy bot updates

## Cost Optimization

- **Right-size instance**: Start with Basic XXS, upgrade if needed
- **Monitor usage**: Use DO's insights to optimize
- **Database**: Consider managed DB only if needed (otherwise use existing)

## Security Best Practices

✅ **Encrypt all sensitive env vars** (API keys, passwords, tokens)  
✅ **Use TELEGRAM_ALLOWED_USERS** if bot is for specific team  
✅ **Enable 2FA** on your DigitalOcean account  
✅ **Rotate tokens** periodically (bot token, API keys)  
✅ **Monitor logs** for suspicious activity  
✅ **Database**: Use read-only user if possible  
✅ **SSL/TLS**: Always use encrypted database connections  

## Rollback

If a deployment breaks:
1. Go to "Deployments" tab
2. Find last working deployment
3. Click "⋯" → "Redeploy"

## Support

- [DigitalOcean Documentation](https://docs.digitalocean.com/products/app-platform/)
- [DigitalOcean Community](https://www.digitalocean.com/community)
- [Support Tickets](https://cloud.digitalocean.com/support/tickets)

## Next Steps

🎉 **Congratulations!** Your Telegram bot is now live and accessible to the world!

Consider:
- Adding more  bot commands
- Implementing user analytics
- Creating a web dashboard for admins
- Setting up monitoring and alerting
- Documenting common queries for your team
