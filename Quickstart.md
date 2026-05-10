# 🚀 Quick Start Guide - FileShare Pro

Get up and running in 60 seconds!

---

## 💻 Running on Your Computer (Easiest)

### Windows
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python shareit_clone.py

# 3. Open browser (automatically opens to http://localhost:49690)
```

### Mac/Linux
```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Run the app
python3 shareit_clone.py

# 3. Open browser to http://localhost:49690
```

---

## 📱 Connecting Your Phone

### Method 1: QR Code (Recommended)
1. Make sure your phone is on the **same WiFi** as your computer
2. Open the app on your computer
3. Use your phone camera to scan the QR code shown
4. Tap the notification to open in browser
5. Done! Start sharing files

### Method 2: Manual Entry
1. Note the IP address shown in the app (e.g., `192.168.1.100:49690`)
2. Open your phone's web browser
3. Type the address in the URL bar
4. Hit Enter
5. Done!

---

## 📤 Sharing Files

### From Phone to PC
1. Connect your phone (see above)
2. Tap the upload area or "Choose Files"
3. Select files from your phone
4. Files automatically transfer to your PC
5. Find them in: `C:\Users\YourName\FileSharePro\uploads\`

### From PC to Phone
1. Copy files to: `C:\Users\YourName\FileSharePro\downloads\`
2. Files appear in "Available for Download" section
3. On your phone, tap "Download" next to the file
4. File downloads to your phone!

---

## 🔧 Creating EXE File (Windows Only)

### Simple Method
```bash
# Just run this:
nuitka.bat

# Wait 5-10 minutes
# Find your EXE in: dist\FileSharePro.exe
```

### What the EXE Does
- ✅ No Python installation needed
- ✅ Double-click to run
- ✅ Share with friends
- ✅ Works on any Windows PC

---

## 🌍 Access from Anywhere (Optional)

Want to access from outside your home network?

### Free Cloud Hosting (5 minutes setup)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/fileshare-pro.git
   git push -u origin main
   ```

2. **Deploy to Render.com**
   - Sign up at [render.com](https://render.com) (free)
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Click "Create Web Service"
   - Wait 2 minutes

3. **Access Anywhere**
   - Your URL: `https://your-app-name.onrender.com`
   - Share with anyone!

📖 **Full instructions**: See `DEPLOYMENT_GUIDE.md`

---

## ❓ Troubleshooting

### "Port already in use"
- The app auto-finds a free port
- Or change `DEFAULT_PORT` in `shareit_clone.py`

### "Phone can't connect"
- ✅ Same WiFi network?
- ✅ Firewall disabled/configured?
- ✅ Correct IP address?

### "Files not uploading"
- Check disk space
- Try smaller files first
- Check antivirus settings

---

## 🎯 Next Steps

1. ✅ **Test it**: Send a file between your phone and PC
2. 📖 **Read README.md**: Full documentation
3. 🚀 **Deploy**: Host on Render.com for remote access
4. 🎨 **Customize**: Change colors, name, features

---

## 📞 Need Help?

- **Full Documentation**: `README.md`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **API Reference**: See endpoints in `shareit_clone.py`

---

**Enjoy seamless file sharing! 🎉**