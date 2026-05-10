# FileShare Pro 🚀

A powerful local network file-sharing application inspired by SHAREit, built with Python Flask. Share files seamlessly between your PC, Android, and iOS devices!

## ✨ Features

- 📱 **Cross-Platform**: Works with Android, iOS, Windows, macOS, Linux
- ⚡ **Lightning Fast**: Transfer files at local network speeds
- 🔒 **Secure**: All transfers happen on your local network
- 📊 **Real-time Stats**: Monitor connected devices and file transfers
- 🎯 **QR Code Connection**: Easy mobile device pairing
- 🌐 **Web Interface**: Beautiful, responsive UI accessible from any browser
- 💾 **Drag & Drop**: Intuitive file upload experience
- 📂 **File Management**: Organize received and shared files

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- All devices must be on the same WiFi network

### Installation

1. **Clone or Download** this repository

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   python shareit_clone.py
   ```

4. **Access the Interface**
   - Open your browser to `http://localhost:49690`
   - On mobile devices, scan the QR code shown on screen

## 🖥️ Creating Standalone Executable (Windows)

### Using Nuitka v4.0.5

1. **Install Nuitka**
   ```bash
   pip install nuitka==4.0.5
   ```

2. **Run the Batch File**
   ```bash
   nuitka.bat
   ```

3. **Find Your Executable**
   - Location: `dist/FileSharePro.exe`
   - Double-click to run - no Python installation needed!

### Manual Nuitka Compilation

```bash
python -m nuitka --standalone --onefile ^
    --enable-plugin=anti-bloat ^
    --include-data-dir=templates=templates ^
    --output-filename=FileSharePro.exe ^
    shareit_clone.py
```

## 📱 Mobile Access

### Method 1: QR Code (Recommended)
1. Open the app on your PC
2. Scan the QR code with your mobile browser
3. Start sharing files!

### Method 2: Manual IP Entry
1. Note your PC's IP address (shown in the app)
2. On your mobile device, open browser
3. Navigate to: `http://[PC_IP]:49690`
4. Example: `http://192.168.1.100:49690`

## 🌍 Remote Access & Hosting

### Option 1: GitHub + Render.com (FREE)

This setup allows you to access your file-sharing service from anywhere!

#### Step 1: Prepare for GitHub

1. **Create `.gitignore`**
   ```gitignore
   __pycache__/
   *.pyc
   *.pyo
   *.pyd
   .Python
   env/
   venv/
   .env
   *.log
   dist/
   build/
   *.egg-info/
   .DS_Store
   ```

2. **Create `Procfile`** (for Render.com)
   ```
   web: python shareit_clone.py
   ```

3. **Update `shareit_clone.py`** - Add this near the bottom of the file:
   ```python
   if __name__ == '__main__':
       port = int(os.environ.get('PORT', DEFAULT_PORT))
       main()
   ```

#### Step 2: Push to GitHub

```bash
# Initialize git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - FileShare Pro"

# Create repository on GitHub (github.com/new)
# Then link and push:
git remote add origin https://github.com/YOUR_USERNAME/fileshare-pro.git
git branch -M main
git push -u origin main
```

#### Step 3: Deploy on Render.com

1. **Sign up** at [render.com](https://render.com) (free account)

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `fileshare-pro` repository

3. **Configure Service**
   - **Name**: `fileshare-pro` (or your choice)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python shareit_clone.py`
   - **Plan**: Select "Free"

4. **Environment Variables** (Optional)
   - Key: `PORT`
   - Value: `10000` (Render's default)

5. **Deploy**
   - Click "Create Web Service"
   - Wait 2-5 minutes for deployment
   - Your app will be live at: `https://fileshare-pro.onrender.com`

#### Step 4: Access Remotely

- **Web**: `https://your-app-name.onrender.com`
- **Mobile**: Open the URL in your mobile browser
- **Share**: Share the URL with anyone on your network

### Option 2: Ngrok (Quick Testing)

For quick remote access without deployment:

```bash
# Install ngrok
# Download from https://ngrok.com/download

# Run your app
python shareit_clone.py

# In another terminal, expose it
ngrok http 49690

# Use the provided URL (e.g., https://abc123.ngrok.io)
```

### Option 3: Local Network Only (Default)

The app works perfectly on your local network without any hosting:
- All devices must be on the same WiFi
- Access via local IP address
- No internet required
- Maximum privacy and speed

## 📂 File Locations

- **Received Files**: `C:\Users\YourName\FileSharePro\uploads\`
- **Shared Files**: `C:\Users\YourName\FileSharePro\downloads\`

To share files with others:
1. Copy files to the downloads folder
2. They'll appear in the "Available for Download" section
3. Mobile users can download them

## 🔧 Configuration

Edit `shareit_clone.py` to customize:

```python
APP_NAME = "FileShare Pro"        # Change app name
DEFAULT_PORT = 49690               # Change port number
MAX_CONTENT_LENGTH = 10 * 1024 * 1024 * 1024  # Max file size (10GB)
```

## 🛠️ API Endpoints

### Connection
- `GET /webuser` - Device connection handshake
- `GET /api/devices` - List connected devices

### File Operations
- `POST /api/upload` - Upload files to PC
- `GET /api/files` - List files available for download
- `GET /api/download/<filename>` - Download file from PC
- `GET /api/received-files` - List received files

### Web Interface
- `GET /` - Main dashboard
- `GET /pc/online.html` - File manager interface

## 🔐 Security Considerations

- **Local Network Only**: By default, only accessible on your local network
- **No Authentication**: Currently no password protection (suitable for trusted networks)
- **File Size Limits**: Configurable max file size to prevent abuse
- **CORS Enabled**: Cross-origin requests allowed for mobile access

### Adding Password Protection (Optional)

Add this to `shareit_clone.py`:

```python
from functools import wraps
from flask import request, jsonify

SECURITY_TOKEN = "your-secret-token"

def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Security-Token')
        if token != SECURITY_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# Apply to routes:
@app.route('/api/upload', methods=['POST'])
@require_token
def upload_file():
    # ... existing code
```

## 🐛 Troubleshooting

### Port Already in Use
The app will automatically find an available port between 49690-49790.

### Firewall Blocking
Add firewall exception:
```bash
# Windows (Run as Administrator)
netsh advfirewall firewall add rule name="FileShare Pro" dir=in action=allow protocol=TCP localport=49690
```

### Mobile Can't Connect
1. Ensure devices are on the same WiFi network
2. Check if firewall is blocking the port
3. Try disabling VPN on mobile device
4. Verify IP address is correct

### Files Not Uploading
1. Check available disk space
2. Verify upload folder permissions
3. Check file size limits
4. Try smaller files first

## 📊 Performance

- **Transfer Speed**: Up to 100+ MB/s on modern WiFi
- **Max File Size**: 10GB (configurable)
- **Concurrent Uploads**: Supports multiple simultaneous transfers
- **Browser Support**: Chrome, Firefox, Safari, Edge

## 🎨 Customization

### Change Theme Colors

Edit the CSS in templates:
```css
/* Change gradient colors */
background: linear-gradient(135deg, #YOUR_COLOR1 0%, #YOUR_COLOR2 100%);
```

### Add Logo

Replace the emoji in templates:
```html
<h1>🚀 FileShare Pro</h1>
<!-- Change to: -->
<h1><img src="your-logo.png"> FileShare Pro</h1>
```

## 📄 License

This project is open source and available for personal and commercial use.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📞 Support

Having issues? 
- Check the Troubleshooting section above
- Review the API documentation
- Check your network configuration

## 🔄 Updates

### Version 1.0.0 (Current)
- ✅ Cross-platform file sharing
- ✅ QR code connection
- ✅ Drag & drop uploads
- ✅ Real-time stats
- ✅ Beautiful web interface

### Planned Features
- 📱 Native mobile apps
- 🔐 Password protection
- 📊 Transfer history
- 🌙 Dark mode
- 🗂️ Folder uploads
- 📝 File preview

## 🌟 Credits

Inspired by SHAREit's excellent file-sharing experience, rebuilt with modern web technologies.

---

**Made with ❤️ for seamless file sharing**

For more information, visit the [GitHub repository](https://github.com/YOUR_USERNAME/fileshare-pro)