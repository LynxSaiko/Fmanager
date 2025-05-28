#!/bin/bash
# Fmanager Installation Script

# Configuration
APP_NAME="fmanager"
INSTALL_DIR="/opt/$APP_NAME"
BIN_DIR="/usr/local/bin"

# Check root
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Create directories
echo "Installing Fmanager to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR"

# Copy files
cp -r ./* "$INSTALL_DIR/"
chmod 644 "$INSTALL_DIR"/*.py
chmod 644 "$INSTALL_DIR"/*.settings

# Install wrapper
echo "Creating executable..."
cp fmanager "$BIN_DIR/"
chmod 755 "$BIN_DIR/fmanager"

# Create desktop entry
echo "Adding desktop integration..."
cat > /usr/share/applications/fmanager.desktop <<EOL
[Desktop Entry]
Name=Fmanager
Comment=Terminal File Manager
Exec=fmanager
Icon=$INSTALL_DIR/icon.png
Terminal=true
Type=Application
Categories=System;FileTools;
Keywords=file;manager;terminal;
EOL

echo "Installation complete. Run with 'fmanager'"
