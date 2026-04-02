#!/bin/bash
set -e

APPDIR="/userdata/system/.dev/apps"
FFDIR="$APPDIR/firefox"

mkdir -p "$APPDIR"
cd "$APPDIR"

echo "Downloading Firefox official (.tar.xz)..."
curl -L "https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=pt-BR" \
     -o firefox.tar.xz

echo "Extracting..."
tar -xJf firefox.tar.xz
rm firefox.tar.xz

echo "Fixing permissions..."
find "$FFDIR" -type f -exec chmod +x {} \;

echo "Firefox installed at $FFDIR"
