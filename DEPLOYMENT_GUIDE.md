# 🚀 Deployment Guide - FileShare Pro

## Complete Step-by-Step Guide for GitHub + Render.com FREE Hosting

---

## 📋 Prerequisites

- Git installed on your computer
- GitHub account (free) - [Sign up here](https://github.com/signup)
- Render.com account (free) - [Sign up here](https://render.com/signup)

---

## Part 1: Setting Up GitHub Repository

### Step 1: Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Fill in repository details:
   - **Repository name**: `fileshare-pro`
   - **Description**: `Local network file sharing application`
   - **Visibility**: Public (required for free Render deployment)
   - ☑️ Skip "Initialize with README" (we already have one)
3. Click **"Create repository"**

### Step 2: Initialize Git Locally

Open Command Prompt/Terminal in your project folder:

```bash
# Initialize git repository
git init

# Add all files
git add .

# Commit files
git commit -m "Initial commit - FileShare Pro v1.0"

# Add remote repository (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/fileshare-pro.git

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main
```

### Step 3: Verify Upload

1. Go to your GitHub repository URL
2. You should see all files uploaded:
   - shareit_clone.py
   - requirements.txt
   - README.md
   - Procfile
   - render.yaml
   - runtime.txt
   - templates/ folder

---

## Part 2: Deploying to Render.com

### Step 1: Sign Up for Render.com

1. Go to [render.com/signup](https://render.com/signup)
2. Sign up using your GitHub account (recommended)
3. Authorize Render to access your GitHub repositories

### Step 2: Create New Web Service

1. Click **"New +"** button (top right)
2. Select **"Web Service"**
3. Click **"Connect Repository"** next to your `fileshare-pro` repo
4. If you don't see it, click **"Configure account"** and grant access

### Step 3: Configure Service Settings

Fill in the following:

| Setting | Value |
|---------|-------|
| **Name** | `fileshare-pro` (or any name you prefer) |
| **Region** | Choose closest to you |
| **Branch** | `main` |
| **Root Directory** | Leave blank |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python shareit_clone.py` |
| **Plan** | **Free** (important!) |

### Step 4: Environment Variables (Optional)

Click **"Advanced"** and add:

```
PORT = 10000
```

(Render automatically sets this, but you can specify it)

### Step 5: Deploy!

1. Click **"Create Web Service"**
2. Wait 2-5 minutes for deployment
3. Watch the build logs (you'll see dependencies installing)
4. When you see "Your service is live 🎉", it's ready!

### Step 6: Get Your URL

Your app will be accessible at:
```
https://fileshare-pro.onrender.com
```
(Replace with your actual service name)

---

## Part 3: Using Your Deployed App

### Access from Anywhere

1. **Desktop Browser**:
   - Visit: `https://your-app-name.onrender.com`
   
2. **Mobile Browser** (Android/iOS):
   - Open browser
   - Navigate to your Render URL
   - Bookmark for easy access

3. **Share QR Code**:
   - The app generates a QR code automatically
   - Others can scan to connect

### Important Notes about Free Tier

⚠️ **Render Free Tier Limitations**:
- Your app will "sleep" after 15 minutes of inactivity
- First request after sleep takes 30-50 seconds to wake up
- 750 hours/month free (enough for continuous use)
- Automatic restarts if app crashes

💡 **Keep Your App Awake**:
Use [UptimeRobot](https://uptimerobot.com) (free) to ping your app every 5 minutes:
1. Sign up at UptimeRobot
2. Add new monitor
3. URL to monitor: `https://your-app.onrender.com`
4. Check interval: 5 minutes

---

## Part 4: Local Network vs Remote Access

### Scenario 1: Local Network Only (Fastest)

**When to use**: You and your devices are on the same WiFi

**How to use**:
```bash
# Run locally on your PC
python shareit_clone.py

# Access from mobile on same WiFi
http://192.168.1.X:49690
```

**Advantages**:
- ⚡ Ultra-fast transfers (100+ MB/s)
- 🔒 Maximum privacy
- 📶 No internet required

### Scenario 2: Remote Access (Anywhere)

**When to use**: Devices on different networks, or accessing from outside home

**How to use**:
```
# Access your Render deployment
https://your-app.onrender.com
```

**Advantages**:
- 🌍 Access from anywhere
- 📱 Share with friends remotely
- ☁️ Always available

**Disadvantages**:
- 🐌 Slower (depends on internet speed)
- 💤 May sleep on free tier
- 📊 Limited by Render's bandwidth

---

## Part 5: Advanced Deployment Options

### Option A: Custom Domain (Render)

1. Purchase domain (e.g., Namecheap, GoDaddy)
2. In Render dashboard → Settings → Custom Domain
3. Add your domain: `fileshare.yourdomain.com`
4. Update DNS records as instructed
5. SSL certificate is automatic!

### Option B: Heroku Alternative

```bash
# Install Heroku CLI
# Download from https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create app
heroku create fileshare-pro

# Deploy
git push heroku main

# Open app
heroku open
```

### Option C: Railway.app

1. Sign up at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Select your repository
4. Auto-deploys (no configuration needed!)
5. Free tier: $5 credit/month

### Option D: Self-Host on VPS

For advanced users (DigitalOcean, AWS, etc):

```bash
# SSH into your VPS
ssh user@your-server-ip

# Install dependencies
sudo apt update
sudo apt install python3 python3-pip

# Clone repository
git clone https://github.com/YOUR_USERNAME/fileshare-pro.git
cd fileshare-pro

# Install requirements
pip3 install -r requirements.txt

# Run with nohup (background)
nohup python3 shareit_clone.py &

# Or use systemd service (recommended)
sudo nano /etc/systemd/system/fileshare.service
```

---

## Part 6: Updating Your Deployment

### When You Make Changes

```bash
# Make your changes to code

# Commit changes
git add .
git commit -m "Description of changes"

# Push to GitHub
git push origin main

# Render automatically redeploys! 🎉
```

---

## Part 7: Monitoring & Troubleshooting

### Check Deployment Status

1. Go to Render dashboard
2. Click your service
3. View **Logs** tab for errors
4. View **Metrics** for usage stats

### Common Issues

**Issue**: App not starting
- **Fix**: Check logs for Python errors
- Verify all files are committed to GitHub

**Issue**: Port binding error
- **Fix**: Ensure app reads PORT from environment:
```python
port = int(os.environ.get('PORT', 49690))
```

**Issue**: Files not uploading
- **Fix**: Render's ephemeral filesystem means uploaded files are lost on restart
- Consider using cloud storage (S3, Cloudinary) for persistence

**Issue**: Slow performance
- **Fix**: Upgrade to paid Render plan ($7/month)
- Or use VPS for better performance

---

## Part 8: Security Best Practices

### For Public Deployments

1. **Add Authentication**:
```python
# Add password protection
from functools import wraps

def check_auth(username, password):
    return username == 'admin' and password == 'your-secret-password'

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response('Login required', 401, 
                          {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated

@app.route('/api/upload', methods=['POST'])
@requires_auth
def upload_file():
    # ... existing code
```

2. **Use Environment Variables**:
```bash
# In Render dashboard, add:
SECRET_KEY = your-random-secret-key
ADMIN_PASSWORD = secure-password-here
```

3. **Rate Limiting**:
```bash
pip install flask-limiter

# In code:
from flask_limiter import Limiter
limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/api/upload', methods=['POST'])
@limiter.limit("10 per minute")
def upload_file():
    # ... existing code
```

---

## 🎉 Congratulations!

You now have:
- ✅ Code on GitHub (version controlled)
- ✅ Live app on Render.com (accessible anywhere)
- ✅ Automatic deployments (push to update)
- ✅ Free hosting (forever!)

**Your app is now live at**: `https://your-app-name.onrender.com`

---

## 📞 Support Resources

- **Render Docs**: [docs.render.com](https://docs.render.com)
- **GitHub Help**: [docs.github.com](https://docs.github.com)
- **Flask Docs**: [flask.palletsprojects.com](https://flask.palletsprojects.com)

---

**Happy Sharing! 🚀**
