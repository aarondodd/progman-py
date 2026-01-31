#!/bin/bash
#
# Build script for Program Manager
# Creates a single-file executable using PyInstaller
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="progman"
DIST_DIR="$SCRIPT_DIR/dist"
BUILD_DIR="$SCRIPT_DIR/build"
VENV_DIR="$SCRIPT_DIR/.venv"
BIN_DIR="$HOME/bin"

echo "=== Program Manager Build Script ==="
echo ""

# Check if we're in a virtual environment, if not activate or create one
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "$VENV_DIR" ]; then
        echo "Activating virtual environment..."
        source "$VENV_DIR/bin/activate"
    else
        echo "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
    fi
fi

# Install dependencies
echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r "$SCRIPT_DIR/requirements.txt"
pip install --quiet pyinstaller

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf "$DIST_DIR" "$BUILD_DIR"

# Run PyInstaller
echo "Building executable with PyInstaller..."
cd "$SCRIPT_DIR"

pyinstaller \
    --name "$APP_NAME" \
    --onefile \
    --windowed \
    --noconfirm \
    --clean \
    --hidden-import=PyQt6 \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtGui \
    --hidden-import=PyQt6.QtWidgets \
    --collect-all=PyQt6 \
    --exclude-module=PyQt6.Qt3D \
    --exclude-module=PyQt6.QtBluetooth \
    --exclude-module=PyQt6.QtDBus \
    --exclude-module=PyQt6.QtDesigner \
    --exclude-module=PyQt6.QtHelp \
    --exclude-module=PyQt6.QtMultimedia \
    --exclude-module=PyQt6.QtMultimediaWidgets \
    --exclude-module=PyQt6.QtNfc \
    --exclude-module=PyQt6.QtOpenGL \
    --exclude-module=PyQt6.QtOpenGLWidgets \
    --exclude-module=PyQt6.QtPdf \
    --exclude-module=PyQt6.QtPdfWidgets \
    --exclude-module=PyQt6.QtPositioning \
    --exclude-module=PyQt6.QtQml \
    --exclude-module=PyQt6.QtQuick \
    --exclude-module=PyQt6.QtQuick3D \
    --exclude-module=PyQt6.QtQuickWidgets \
    --exclude-module=PyQt6.QtRemoteObjects \
    --exclude-module=PyQt6.QtSensors \
    --exclude-module=PyQt6.QtSerialPort \
    --exclude-module=PyQt6.QtSpatialAudio \
    --exclude-module=PyQt6.QtSql \
    --exclude-module=PyQt6.QtStateMachine \
    --exclude-module=PyQt6.QtSvg \
    --exclude-module=PyQt6.QtSvgWidgets \
    --exclude-module=PyQt6.QtTest \
    --exclude-module=PyQt6.QtTextToSpeech \
    --exclude-module=PyQt6.QtWebChannel \
    --exclude-module=PyQt6.QtWebSockets \
    --exclude-module=PyQt6.QtXml \
    --exclude-module=PyQt6.lupdate \
    --exclude-module=PyQt6.uic \
    main.py

# Check if build succeeded
if [ ! -f "$DIST_DIR/$APP_NAME" ]; then
    echo "ERROR: Build failed - executable not found"
    exit 1
fi

echo ""
echo "Build successful!"
echo "Executable: $DIST_DIR/$APP_NAME"

# Create ~/bin if it doesn't exist
if [ ! -d "$BIN_DIR" ]; then
    echo "Creating $BIN_DIR..."
    mkdir -p "$BIN_DIR"
fi

# Copy to ~/bin
# Remove old executable first (allows replacing even if currently running)
echo "Installing to $BIN_DIR/$APP_NAME..."
rm -f "$BIN_DIR/$APP_NAME"
cp "$DIST_DIR/$APP_NAME" "$BIN_DIR/$APP_NAME"
chmod +x "$BIN_DIR/$APP_NAME"

echo ""
echo "=== Installation Complete ==="
echo "Executable installed to: $BIN_DIR/$APP_NAME"
echo ""
echo "Make sure $BIN_DIR is in your PATH:"
echo "  export PATH=\"\$HOME/bin:\$PATH\""
echo ""
