"""
FileShare Pro - Cloud-Ready File Sharing Application
Fixed version for Render deployment
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
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import qrcode
from io import BytesIO
import base64

# Configuration
APP_NAME = "FileShare Pro"
VERSION = "1.0.1"
DEFAULT_PORT = 49690
DEVICE_TIMEOUT = timedelta(minutes=10)

# Use /tmp for cloud deployments or home directory for local
if os.environ.get('RENDER'):
    BASE_DIR = Path("/tmp/FileSharePro")
else:
    BASE_DIR = Path.home() / "FileSharePro"

UPLOAD_FOLDER = BASE_DIR / "uploads"
DOWNLOAD_FOLDER = BASE_DIR / "downloads"

# Ensure directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Flask app setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['DOWNLOAD_FOLDER'] = str(DOWNLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
CORS(app)

# Global state
connected_devices = {}
pc_id = str(uuid.uuid4()).replace('-', '').upper() + "_web"
pc_name = f"{platform.node()}'s PC"


def get_local_ip():
    """Get the active local IP address"""
    try:
        # Try hostname resolution first
        ip = socket.gethostbyname(socket.gethostname())
        if ip.startswith("127."):
            # If it resolves to localhost, force external check
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        return ip
    except Exception:
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


def cleanup_devices():
    now = datetime.now()
    to_remove = []

    for k, v in connected_devices.items():
        last = datetime.fromisoformat(v['connected_at'])
        if now - last > DEVICE_TIMEOUT:
            to_remove.append(k)

    for k in to_remove:
        del connected_devices[k]

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
    """Handle large file uploads safely"""

    if 'file' not in request.files:
        return jsonify({
            "status": -1,
            "error": "No file provided"
        }), 400

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

        try:

            # Stream write file in chunks (GOOD for big videos)
            with open(filepath, "wb") as f:

                while True:
                    chunk = file.stream.read(1024 * 1024)  # 1MB chunks

                    if not chunk:
                        break

                    f.write(chunk)

            uploaded_files.append({
                "name": filepath.name,
                "size": filepath.stat().st_size,
                "path": str(filepath),
                "url": f"/uploads/{filepath.name}"
            })

        except Exception as e:

            return jsonify({
                "status": -1,
                "error": str(e)
            }), 500

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


# ADD THIS HERE
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(
        UPLOAD_FOLDER,
        filename,
        as_attachment=True
    )


# ADD THIS TOO
@app.route('/uploads')
def uploads_list():
    html = "<h1>Uploaded Files</h1><ul>"

    for file_path in UPLOAD_FOLDER.iterdir():
        if file_path.is_file():
            name = file_path.name
            html += f'<li><a href="/uploads/{name}">{name}</a></li>'

    html += "</ul>"
    return html

# Web Interface Routes
@app.route('/')
def index():
    """Main landing page with file upload interface"""
    # Get the base URL (works for both local and cloud)
    if request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
        base_url = f"http://{get_local_ip()}:{request.host.split(':')[-1]}"
    else:
        # Cloud deployment
        base_url = request.host_url.rstrip('/')
    
    connection_url = f"{base_url}/connect"
    qr_code = generate_qr_code(connection_url)
    
    return render_template_string(TEMPLATE_MAIN, 
                                   app_name=APP_NAME,
                                   version=VERSION,
                                   connection_url=connection_url,
                                   qr_code=qr_code,
                                   is_cloud=bool(os.environ.get('RENDER')))

@app.route('/connect')
def connect_page():
    """Mobile-friendly connection page"""
    return render_template_string(TEMPLATE_MOBILE)


@app.route('/pc/online.html')
def online_page():
    """Legacy connection page for compatibility"""
    return connect_page()


# HTML Templates
TEMPLATE_MAIN = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ app_name }} - Share Files Instantly</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📁</text></svg>">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .header .version {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .qr-section {
            text-align: center;
        }
        
        .qr-code-img {
            max-width: 300px;
            margin: 20px auto;
            display: block;
            border: 3px solid #667eea;
            border-radius: 8px;
            padding: 10px;
            background: white;
        }
        
        .upload-zone {
            border: 3px dashed #667eea;
            border-radius: 8px;
            padding: 50px 20px;
            text-align: center;
            background: #f8f9ff;
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .upload-zone:hover {
            background: #f0f2ff;
            border-color: #764ba2;
        }
        
        .upload-zone.drag-over {
            background: #e8ebff;
            border-color: #764ba2;
            transform: scale(1.02);
        }
        
        .file-input {
            display: none;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        .btn-small {
            padding: 8px 20px;
            font-size: 0.9em;
        }
        
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #f0f0f0;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        
        .file-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 10px;
            transition: all 0.3s;
        }
        
        .file-item:hover {
            background: #f8f9ff;
            border-color: #667eea;
        }
        
        .file-info {
            flex: 1;
        }
        
        .file-name {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        
        .file-meta {
            font-size: 0.85em;
            color: #666;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 1.1em;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin-top: 10px;
        }
        
        .status-cloud {
            background: #e3f2fd;
            color: #1976d2;
        }
        
        .status-local {
            background: #f3e5f5;
            color: #7b1fa2;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }
            .section {
                padding: 20px;
            }
            .qr-code-img {
                max-width: 200px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📁 {{ app_name }}</h1>
        <div class="version">v{{ version }}</div>
        {% if is_cloud %}
        <div class="status-badge status-cloud">☁️ Cloud Mode</div>
        {% else %}
        <div class="status-badge status-local">🏠 Local Network</div>
        {% endif %}
    </div>
    
    <div class="container">
        <!-- QR Code Section -->
        <div class="section qr-section">
            <h2>📱 Connect Your Mobile Device</h2>
            <p>Scan this QR code with your mobile device</p>
            <img src="{{ qr_code }}" alt="Connection QR Code" class="qr-code-img">
            <p style="margin-top: 15px; color: #666; font-size: 0.9em;">
                Or visit directly: <strong style="color: #667eea;">{{ connection_url }}</strong>
            </p>
        </div>
        
        <!-- Upload Section -->
        <div class="section">
            <h2>📤 Upload Files</h2>
            <div class="upload-zone" id="uploadZone">
                <p style="font-size: 1.2em; margin-bottom: 10px;">📁 Drag & Drop files here</p>
                <p style="color: #999;">or</p>
                <button class="btn" style="margin-top: 10px;" onclick="document.getElementById('fileInput').click()">Choose Files</button>
                <input type="file" id="fileInput" class="file-input" multiple>
            </div>
            <div id="uploadProgress" style="display: none; margin-top: 20px;">
                <p id="uploadStatus" style="margin-bottom: 10px;">Uploading...</p>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill">0%</div>
                </div>
            </div>
        </div>
        
        <!-- Received Files -->
        <div class="section">
            <h2>📥 Received Files</h2>
            <div id="receivedFiles" class="file-list">
                <div class="empty-state">
                    <p>No files received yet</p>
                    <p style="font-size: 0.9em; margin-top: 10px; color: #bbb;">Files uploaded will appear here</p>
                </div>
            </div>
        </div>
        
        <!-- Available Files to Download -->
        <div class="section">
            <h2>📂 Files Available for Download</h2>
            <div id="availableFiles" class="file-list">
                <div class="empty-state">
                    <p>No files available</p>
                    <p style="font-size: 0.9em; margin-top: 10px; color: #bbb;">Add files to share with devices</p>
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
            progressFill.textContent = '0%';
            
            try {
                const xhr = new XMLHttpRequest();
                
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percent = Math.round((e.loaded / e.total) * 100);
                        progressFill.style.width = percent + '%';
                        progressFill.textContent = percent + '%';
                    }
                });
                
                xhr.addEventListener('load', () => {
                    if (xhr.status === 200) {
                        uploadStatus.textContent = '✅ Upload complete!';
                        progressFill.style.width = '100%';
                        progressFill.textContent = '100%';
                        setTimeout(() => {
                            uploadProgress.style.display = 'none';
                            progressFill.style.width = '0%';
                            fileInput.value = '';
                            loadReceivedFiles();
                        }, 2000);
                    } else {
                        uploadStatus.textContent = '❌ Upload failed!';
                    }
                });
                
                xhr.open('POST', '/api/upload');
                xhr.send(formData);
            } catch (err) {
                uploadStatus.textContent = '❌ Error: ' + err.message;
            }
        }
        
        async function loadReceivedFiles() {
            try {
                const response = await fetch('/api/received-files');
                const data = await response.json();
                
                const container = document.getElementById('receivedFiles');
                
                if (data.files.length === 0) {
                    container.innerHTML = '<div class="empty-state"><p>No files received yet</p><p style="font-size: 0.9em; margin-top: 10px; color: #bbb;">Files uploaded will appear here</p></div>';
                    return;
                }
                
                container.innerHTML = data.files.map(file => `
                    <div class="file-item">
                        <div class="file-info">
                            <div class="file-name">📄 ${escapeHtml(file.name)}</div>
                            <div class="file-meta">${formatBytes(file.size)} • ${new Date(file.received).toLocaleString()}</div>
                        </div>
                        <a href="/api/download/${encodeURIComponent(file.name)}" download>
                            <button class="btn btn-small">Download</button>
                        </a>
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
                    container.innerHTML = '<div class="empty-state"><p>No files available</p><p style="font-size: 0.9em; margin-top: 10px; color: #bbb;">Add files to share with devices</p></div>';
                    return;
                }
                
                container.innerHTML = data.files.map(file => `
                    <div class="file-item">
                        <div class="file-info">
                            <div class="file-name">📄 ${escapeHtml(file.name)}</div>
                            <div class="file-meta">${formatBytes(file.size)} • Modified: ${new Date(file.modified).toLocaleString()}</div>
                        </div>
                        <button class="btn btn-small" onclick="downloadFile('${escapeHtml(file.name)}')">Download</button>
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
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function downloadFile(filename) {
            window.location.href = `/api/download/${encodeURIComponent(filename)}`;
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

TEMPLATE_MOBILE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Files - FileShare Pro</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📱</text></svg>">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 500px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .card {
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }
        
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 12px;
            padding: 40px 20px;
            text-align: center;
            background: #f8f9ff;
            margin-bottom: 20px;
            transition: all 0.3s;
        }
        
        .upload-area.drag-over {
            background: #e8ebff;
            border-color: #764ba2;
            transform: scale(1.02);
        }
        
        .upload-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1.1em;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s;
        }
        
        .btn:active {
            transform: scale(0.98);
        }
        
        .file-input {
            display: none;
        }
        
        .progress {
            margin-top: 20px;
            display: none;
        }
        
        .progress-bar {
            width: 100%;
            height: 40px;
            background: #f0f0f0;
            border-radius: 20px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .file-list {
            margin-top: 20px;
        }
        
        .file-item {
            background: #f8f9ff;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .file-item-icon {
            font-size: 1.5em;
        }
        
        .file-item-info {
            flex: 1;
        }
        
        .file-item-name {
            font-weight: 600;
            color: #333;
            word-break: break-word;
        }
        
        .file-item-size {
            font-size: 0.85em;
            color: #666;
        }
        
        .remove-btn {
            background: #ff4757;
            color: white;
            border: none;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2em;
        }
        
        .success-message {
            background: #4caf50;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            text-align: center;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 FileShare Pro</h1>
            <p>Upload files to share</p>
        </div>
        
        <div class="card">
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">📁</div>
                <p style="font-size: 1.1em; margin-bottom: 10px;">Tap to select files</p>
                <p style="color: #666; font-size: 0.9em;">or drag and drop here</p>
            </div>
            
            <input type="file" id="fileInput" class="file-input" multiple>
            
            <button class="btn" onclick="document.getElementById('fileInput').click()">
                Choose Files
            </button>
            
            <div id="fileList" class="file-list"></div>
            
            <button class="btn" id="uploadBtn" style="display: none; margin-top: 20px;">
                Upload Selected Files
            </button>
            
            <div class="progress" id="progress">
                <p id="progressText" style="text-align: center; margin-bottom: 10px;">Uploading...</p>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill">0%</div>
                </div>
            </div>
            
            <div class="success-message" id="successMessage">
                ✅ Files uploaded successfully!
            </div>
        </div>
    </div>
    
    <script>
        let selectedFiles = [];
        
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const fileList = document.getElementById('fileList');
        const uploadBtn = document.getElementById('uploadBtn');
        const progress = document.getElementById('progress');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const successMessage = document.getElementById('successMessage');
        
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            handleFiles(e.dataTransfer.files);
        });
        
        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });
        
        function handleFiles(files) {
            selectedFiles = Array.from(files);
            displayFiles();
            uploadBtn.style.display = selectedFiles.length > 0 ? 'block' : 'none';
        }
        
        function displayFiles() {
            fileList.innerHTML = selectedFiles.map((file, index) => `
                <div class="file-item">
                    <div class="file-item-icon">📄</div>
                    <div class="file-item-info">
                        <div class="file-item-name">${escapeHtml(file.name)}</div>
                        <div class="file-item-size">${formatBytes(file.size)}</div>
                    </div>
                    <button class="remove-btn" onclick="removeFile(${index})">×</button>
                </div>
            `).join('');
        }
        
        function removeFile(index) {
            selectedFiles.splice(index, 1);
            displayFiles();
            uploadBtn.style.display = selectedFiles.length > 0 ? 'block' : 'none';
        }
        
        uploadBtn.addEventListener('click', uploadFiles);
        
        async function uploadFiles() {
            if (selectedFiles.length === 0) return;
            
            const formData = new FormData();
            selectedFiles.forEach(file => {
                formData.append('file', file);
            });
            
            progress.style.display = 'block';
            uploadBtn.disabled = true;
            progressText.textContent = `Uploading ${selectedFiles.length} file(s)...`;
            
            try {
                const xhr = new XMLHttpRequest();
                
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percent = Math.round((e.loaded / e.total) * 100);
                        progressFill.style.width = percent + '%';
                        progressFill.textContent = percent + '%';
                    }
                });
                
                xhr.addEventListener('load', () => {
                    if (xhr.status === 200) {
                        progressText.textContent = '✅ Upload complete!';
                        successMessage.style.display = 'block';
                        setTimeout(() => {
                            progress.style.display = 'none';
                            successMessage.style.display = 'none';
                            selectedFiles = [];
                            fileList.innerHTML = '';
                            uploadBtn.style.display = 'none';
                            uploadBtn.disabled = false;
                            fileInput.value = '';
                            progressFill.style.width = '0%';
                        }, 3000);
                    } else {
                        progressText.textContent = '❌ Upload failed!';
                        uploadBtn.disabled = false;
                    }
                });
                
                xhr.open('POST', '/api/upload');
                xhr.send(formData);
            } catch (err) {
                progressText.textContent = '❌ Error: ' + err.message;
                uploadBtn.disabled = false;
            }
        }
        
        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
"""


def main():
    """Main entry point"""
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    
    print(f"\n{'='*60}")
    print(f"  {APP_NAME} v{VERSION}")
    print(f"{'='*60}")
    
    if os.environ.get('RENDER'):
        print(f"\n  ☁️  Running in CLOUD mode on Render")
        print(f"  🌍 Access at: https://filesharepro-dap0.onrender.com")
    else:
        local_ip = get_local_ip()
        print(f"\n  🏠 Running in LOCAL mode")
        print(f"  🌐 Local:   http://localhost:{port}")
        print(f"  🌍 Network: http://{local_ip}:{port}")
    
    print(f"\n  📁 Uploads:   {UPLOAD_FOLDER}")
    print(f"  📂 Downloads: {DOWNLOAD_FOLDER}")
    print(f"\n{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    main()