"""
FileShare Pro - Local Network File Sharing Application
A SHAREit-like application for sharing files between devices
"""

import os
import sys
import json
import socket
import uuid
import threading
import platform
import webbrowser
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import qrcode
from io import BytesIO
import base64

# Configuration
APP_NAME = "FileShare Pro"
VERSION = "1.0.0"
DEFAULT_PORT = 49690
UPLOAD_FOLDER = Path.home() / "FileSharePro" / "uploads"
DOWNLOAD_FOLDER = Path.home() / "FileSharePro" / "downloads"

# Ensure directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Flask app setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['DOWNLOAD_FOLDER'] = str(DOWNLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB max file size
CORS(app)

# Global state
connected_devices = {}
pc_id = str(uuid.uuid4()).replace('-', '').upper() + "_web"
pc_name = f"{platform.node()}'s PC"


def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def generate_qr_code(url):
    """Generate QR code for easy mobile connection"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


# API Routes
@app.route('/webuser', methods=['GET', 'POST'])
def webuser():
    """Handle device connection - similar to SHAREit API"""
    if request.method == 'GET':
        cid = request.args.get('cid', '')
        name = request.args.get('name', 'Unknown Device')
        os_type = request.args.get('os', 'unknown')
        dev = request.args.get('dev', 'Mobile')
        
        device_id = cid if cid else str(uuid.uuid4())
        
        # Store connected device
        connected_devices[device_id] = {
            'name': name,
            'os': os_type,
            'device': dev,
            'connected_at': datetime.now().isoformat(),
            'ip': request.remote_addr
        }
        
        return jsonify({
            "status": 0,
            "os": os_type,
            "pc_ip": get_local_ip(),
            "pc_id": pc_id,
            "pc_name": pc_name
        })
    
    return jsonify({"status": -1, "error": "Method not allowed"}), 405


@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get list of connected devices"""
    return jsonify({
        "status": 0,
        "devices": connected_devices,
        "count": len(connected_devices)
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file uploads from mobile devices"""
    if 'file' not in request.files:
        return jsonify({"status": -1, "error": "No file provided"}), 400
    
    files = request.files.getlist('file')
    uploaded_files = []
    
    for file in files:
        if file.filename == '':
            continue
        
        filename = secure_filename(file.filename)
        filepath = UPLOAD_FOLDER / filename
        
        # Handle duplicate filenames
        counter = 1
        base_name = filepath.stem
        extension = filepath.suffix
        while filepath.exists():
            filepath = UPLOAD_FOLDER / f"{base_name}_{counter}{extension}"
            counter += 1
        
        file.save(str(filepath))
        uploaded_files.append({
            "name": filepath.name,
            "size": filepath.stat().st_size,
            "path": str(filepath)
        })
    
    return jsonify({
        "status": 0,
        "message": f"Uploaded {len(uploaded_files)} file(s)",
        "files": uploaded_files
    })


@app.route('/api/files', methods=['GET'])
def list_files():
    """List files in downloads folder available for sharing"""
    files = []
    for file_path in DOWNLOAD_FOLDER.iterdir():
        if file_path.is_file():
            files.append({
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                "download_url": f"/api/download/{file_path.name}"
            })
    
    return jsonify({
        "status": 0,
        "files": files,
        "count": len(files)
    })


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download file from PC to mobile"""
    try:
        return send_from_directory(
            app.config['DOWNLOAD_FOLDER'],
            filename,
            as_attachment=True
        )
    except FileNotFoundError:
        return jsonify({"status": -1, "error": "File not found"}), 404


@app.route('/api/received-files', methods=['GET'])
def list_received_files():
    """List files received from mobile devices"""
    files = []
    for file_path in UPLOAD_FOLDER.iterdir():
        if file_path.is_file():
            files.append({
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "received": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                "path": str(file_path)
            })
    
    return jsonify({
        "status": 0,
        "files": files,
        "count": len(files)
    })


# Web Interface Routes
@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')


@app.route('/pc/online.html')
def online_page():
    """Connection page for mobile devices"""
    local_ip = get_local_ip()
    port = request.host.split(':')[1] if ':' in request.host else DEFAULT_PORT
    connection_url = f"http://{local_ip}:{port}/webuser?cid=&name=&os=&dev=PC"
    qr_code = generate_qr_code(connection_url)
    
    return render_template('online.html', 
                         ip=local_ip, 
                         port=port,
                         qr_code=qr_code,
                         connection_url=connection_url)


@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)


# HTML Templates (embedded for single-file distribution)
TEMPLATE_INDEX = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ app_name }} - Share Files Instantly</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 900px;
            width: 90%;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        
        .connection-info {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .ip-address {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin: 20px 0;
        }
        
        .qr-container {
            margin: 30px auto;
            display: inline-block;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .qr-container img {
            max-width: 250px;
            height: auto;
        }
        
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .feature-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 25px;
            color: white;
            text-align: center;
            transition: transform 0.3s;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
        }
        
        .feature-card h3 {
            margin-bottom: 10px;
            font-size: 1.3em;
        }
        
        .feature-card p {
            opacity: 0.9;
            line-height: 1.6;
        }
        
        .stats {
            display: flex;
            justify-content: space-around;
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
            margin: 10px;
        }
        
        .btn:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        .instructions {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 20px;
            margin-top: 30px;
            border-radius: 5px;
        }
        
        .instructions h3 {
            color: #1976d2;
            margin-bottom: 15px;
        }
        
        .instructions ol {
            margin-left: 20px;
            line-height: 1.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 FileShare Pro</h1>
            <p>Share files seamlessly across all your devices</p>
        </div>
        
        <div class="connection-info">
            <h2>Your Connection Address</h2>
            <div class="ip-address" id="ipAddress">Loading...</div>
            <p>Scan the QR code below with your mobile device</p>
            <div class="qr-container">
                <img id="qrCode" src="" alt="QR Code">
            </div>
        </div>
        
        <div class="features">
            <div class="feature-card">
                <h3>📱 Cross-Platform</h3>
                <p>Works with Android, iOS, and all major platforms</p>
            </div>
            <div class="feature-card">
                <h3>⚡ Lightning Fast</h3>
                <p>Transfer files at local network speeds</p>
            </div>
            <div class="feature-card">
                <h3>🔒 Secure</h3>
                <p>All transfers happen on your local network</p>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number" id="deviceCount">0</div>
                <div class="stat-label">Connected Devices</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="fileCount">0</div>
                <div class="stat-label">Files Shared</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="receivedCount">0</div>
                <div class="stat-label">Files Received</div>
            </div>
        </div>
        
        <div class="instructions">
            <h3>How to Connect</h3>
            <ol>
                <li>Make sure your mobile device is on the same WiFi network</li>
                <li>Open your mobile browser and scan the QR code above</li>
                <li>Or manually enter the IP address shown above</li>
                <li>Start sharing files instantly!</li>
            </ol>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="/pc/online.html" class="btn">Open File Manager</a>
        </div>
    </div>
    
    <script>
        async function updateStats() {
            try {
                const [devicesRes, filesRes, receivedRes] = await Promise.all([
                    fetch('/api/devices'),
                    fetch('/api/files'),
                    fetch('/api/received-files')
                ]);
                
                const devices = await devicesRes.json();
                const files = await filesRes.json();
                const received = await receivedRes.json();
                
                document.getElementById('deviceCount').textContent = devices.count || 0;
                document.getElementById('fileCount').textContent = files.count || 0;
                document.getElementById('receivedCount').textContent = received.count || 0;
            } catch (err) {
                console.error('Error updating stats:', err);
            }
        }
        
        async function loadConnectionInfo() {
            try {
                const response = await fetch('/pc/online.html');
                const html = await response.text();
                
                // Extract IP and QR code from response
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                const ipElement = doc.querySelector('.ip-display');
                const qrElement = doc.querySelector('#qrCodeImg');
                
                if (ipElement) {
                    document.getElementById('ipAddress').textContent = ipElement.textContent;
                }
                
                if (qrElement) {
                    document.getElementById('qrCode').src = qrElement.src;
                }
            } catch (err) {
                document.getElementById('ipAddress').textContent = window.location.host;
            }
        }
        
        loadConnectionInfo();
        updateStats();
        setInterval(updateStats, 3000);
    </script>
</body>
</html>
"""

TEMPLATE_ONLINE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FileShare Pro - File Manager</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 1.8em;
        }
        
        .ip-display {
            font-size: 1.2em;
            margin-top: 10px;
            opacity: 0.95;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .section {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .section h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .upload-zone {
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: #f8f9fa;
        }
        
        .upload-zone:hover, .upload-zone.drag-over {
            background: #e3f2fd;
            border-color: #764ba2;
        }
        
        .upload-zone p {
            font-size: 1.2em;
            color: #666;
            margin: 10px 0;
        }
        
        .file-input {
            display: none;
        }
        
        .file-list {
            margin-top: 20px;
        }
        
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 10px;
            transition: all 0.3s;
        }
        
        .file-item:hover {
            background: #e3f2fd;
            transform: translateX(5px);
        }
        
        .file-info {
            flex-grow: 1;
        }
        
        .file-name {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        
        .file-meta {
            font-size: 0.9em;
            color: #666;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 1em;
        }
        
        .btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-small {
            padding: 8px 15px;
            font-size: 0.9em;
        }
        
        .progress-bar {
            width: 100%;
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
        }
        
        .qr-section {
            text-align: center;
            padding: 20px;
        }
        
        .qr-code-img {
            max-width: 300px;
            margin: 20px auto;
            display: block;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        
        .empty-state svg {
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            opacity: 0.3;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .section {
                padding: 15px;
            }
            
            .file-item {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .btn {
                width: 100%;
                margin-top: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📁 FileShare Pro</h1>
        <div class="ip-display">Connected: {{ ip }}:{{ port }}</div>
    </div>
    
    <div class="container">
        <!-- QR Code Section -->
        <div class="section qr-section">
            <h2>📱 Connect Your Device</h2>
            <p>Scan this QR code with your mobile device</p>
            <img src="{{ qr_code }}" alt="Connection QR Code" class="qr-code-img" id="qrCodeImg">
            <p style="margin-top: 15px; color: #666;">Or visit: <strong>{{ connection_url }}</strong></p>
        </div>
        
        <!-- Upload Section -->
        <div class="section">
            <h2>📤 Send Files to This PC</h2>
            <div class="upload-zone" id="uploadZone">
                <p>📁 Drag & Drop files here</p>
                <p style="font-size: 1em;">or</p>
                <button class="btn" onclick="document.getElementById('fileInput').click()">Choose Files</button>
                <input type="file" id="fileInput" class="file-input" multiple>
            </div>
            <div id="uploadProgress" style="display: none;">
                <p id="uploadStatus">Uploading...</p>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
            </div>
        </div>
        
        <!-- Received Files -->
        <div class="section">
            <h2>📥 Received Files</h2>
            <div id="receivedFiles" class="file-list">
                <div class="empty-state">
                    <p>No files received yet</p>
                </div>
            </div>
        </div>
        
        <!-- Available Files to Download -->
        <div class="section">
            <h2>📂 Files Available for Download</h2>
            <div id="availableFiles" class="file-list">
                <div class="empty-state">
                    <p>No files available</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        const uploadProgress = document.getElementById('uploadProgress');
        const progressFill = document.getElementById('progressFill');
        const uploadStatus = document.getElementById('uploadStatus');
        
        // Drag and drop handlers
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('drag-over');
        });
        
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('drag-over');
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            uploadFiles(files);
        });
        
        fileInput.addEventListener('change', (e) => {
            uploadFiles(e.target.files);
        });
        
        async function uploadFiles(files) {
            if (files.length === 0) return;
            
            const formData = new FormData();
            for (let file of files) {
                formData.append('file', file);
            }
            
            uploadProgress.style.display = 'block';
            uploadStatus.textContent = `Uploading ${files.length} file(s)...`;
            
            try {
                const xhr = new XMLHttpRequest();
                
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percent = (e.loaded / e.total) * 100;
                        progressFill.style.width = percent + '%';
                    }
                });
                
                xhr.addEventListener('load', () => {
                    if (xhr.status === 200) {
                        uploadStatus.textContent = 'Upload complete!';
                        setTimeout(() => {
                            uploadProgress.style.display = 'none';
                            progressFill.style.width = '0%';
                            fileInput.value = '';
                            loadReceivedFiles();
                        }, 2000);
                    } else {
                        uploadStatus.textContent = 'Upload failed!';
                    }
                });
                
                xhr.open('POST', '/api/upload');
                xhr.send(formData);
            } catch (err) {
                uploadStatus.textContent = 'Error: ' + err.message;
            }
        }
        
        async function loadReceivedFiles() {
            try {
                const response = await fetch('/api/received-files');
                const data = await response.json();
                
                const container = document.getElementById('receivedFiles');
                
                if (data.files.length === 0) {
                    container.innerHTML = '<div class="empty-state"><p>No files received yet</p></div>';
                    return;
                }
                
                container.innerHTML = data.files.map(file => `
                    <div class="file-item">
                        <div class="file-info">
                            <div class="file-name">📄 ${file.name}</div>
                            <div class="file-meta">${formatBytes(file.size)} • ${new Date(file.received).toLocaleString()}</div>
                        </div>
                        <button class="btn btn-small" onclick="openFile('${file.path}')">Open</button>
                    </div>
                `).join('');
            } catch (err) {
                console.error('Error loading received files:', err);
            }
        }
        
        async function loadAvailableFiles() {
            try {
                const response = await fetch('/api/files');
                const data = await response.json();
                
                const container = document.getElementById('availableFiles');
                
                if (data.files.length === 0) {
                    container.innerHTML = '<div class="empty-state"><p>No files available</p></div>';
                    return;
                }
                
                container.innerHTML = data.files.map(file => `
                    <div class="file-item">
                        <div class="file-info">
                            <div class="file-name">📄 ${file.name}</div>
                            <div class="file-meta">${formatBytes(file.size)} • Modified: ${new Date(file.modified).toLocaleString()}</div>
                        </div>
                        <button class="btn btn-small" onclick="downloadFile('${file.name}')">Download</button>
                    </div>
                `).join('');
            } catch (err) {
                console.error('Error loading available files:', err);
            }
        }
        
        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }
        
        function openFile(path) {
            alert('File location: ' + path);
        }
        
        function downloadFile(filename) {
            window.location.href = `/api/download/${filename}`;
        }
        
        // Load files on page load
        loadReceivedFiles();
        loadAvailableFiles();
        
        // Refresh every 5 seconds
        setInterval(() => {
            loadReceivedFiles();
            loadAvailableFiles();
        }, 5000);
    </script>
</body>
</html>
"""


def create_templates():
    """Create template directory and files"""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    (templates_dir / "index.html").write_text(TEMPLATE_INDEX)
    (templates_dir / "online.html").write_text(TEMPLATE_ONLINE)


def open_browser(port):
    """Open browser after a short delay"""
    import time
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{port}')


def main():
    """Main entry point"""
    port = DEFAULT_PORT
    
    # Check if port is available
    for attempt_port in range(DEFAULT_PORT, DEFAULT_PORT + 100):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', attempt_port))
        sock.close()
        if result != 0:
            port = attempt_port
            break
    
    create_templates()
    
    local_ip = get_local_ip()
    print(f"\n{'='*60}")
    print(f"  {APP_NAME} v{VERSION}")
    print(f"{'='*60}")
    print(f"\n  🌐 Local:   http://localhost:{port}")
    print(f"  🌍 Network: http://{local_ip}:{port}")
    print(f"\n  📁 Uploads:   {UPLOAD_FOLDER}")
    print(f"  📂 Downloads: {DOWNLOAD_FOLDER}")
    print(f"\n{'='*60}\n")
    
    # Open browser in background
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down FileShare Pro...")
        sys.exit(0)


if __name__ == '__main__':
    main()