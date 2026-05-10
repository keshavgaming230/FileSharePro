#!/bin/bash

# FileShare Pro - Nuitka Compilation Script (Linux/Mac)
# This script compiles the Python application into a standalone executable

echo "========================================"
echo "  FileShare Pro - Nuitka Compiler"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

echo "Python version:"
python3 --version

# Check if Nuitka is installed
if ! pip3 show nuitka &> /dev/null; then
    echo "Nuitka not found. Installing Nuitka v4.0.5..."
    pip3 install nuitka==4.0.5
fi

echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

echo ""
echo "Starting compilation..."
echo "This may take several minutes..."
echo ""

# Nuitka compilation command
python3 -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=anti-bloat \
    --include-data-dir=templates=templates \
    --nofollow-import-to=tkinter \
    --nofollow-import-to=matplotlib \
    --nofollow-import-to=numpy \
    --nofollow-import-to=pandas \
    --assume-yes-for-downloads \
    --output-dir=dist \
    --output-filename=FileSharePro \
    shareit_clone.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Compilation failed!"
    exit 1
fi

echo ""
echo "========================================"
echo "  Compilation Complete!"
echo "========================================"
echo ""
echo "Your executable is located at:"
echo "dist/FileSharePro"
echo ""
echo "Make it executable:"
echo "chmod +x dist/FileSharePro"
echo ""
echo "Run it:"
echo "./dist/FileSharePro"
echo ""