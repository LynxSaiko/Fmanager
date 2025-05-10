#!/bin/bash
# Fmanager Uninstaller

if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

echo "Removing Fmanager..."
rm -rf /opt/fmanager
rm -f /usr/local/bin/fmanager
rm -f /usr/share/applications/fmanager.desktop

echo "Fmanager has been completely removed"