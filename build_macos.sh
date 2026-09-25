#!/bin/sh
set -eu

APP_NAME="CORDHISK-App-v3.0"
OUTPUT_DIR="CORDHISK_App_v3_MacOS"
PYTHON_BIN="${PYTHON_BIN:-python}"
rm -rf "$OUTPUT_DIR" dist
"$PYTHON_BIN" -m PyInstaller --noconfirm --clean --onedir --windowed --distpath "$OUTPUT_DIR" --name "$APP_NAME" \
	--exclude-module PyQt5 --exclude-module PySide6 --exclude-module PyQt6 --exclude-module tkinter \
	launcher.py
rm -rf "$OUTPUT_DIR/$APP_NAME"
rm -rf "$OUTPUT_DIR/memory_files"
cp -R memory_files "$OUTPUT_DIR/memory_files"
rm -rf "$OUTPUT_DIR/$APP_NAME.app/Contents/Resources/memory_files"
mkdir -p "$OUTPUT_DIR/$APP_NAME.app/Contents/Resources"
cp -R memory_files "$OUTPUT_DIR/$APP_NAME.app/Contents/Resources/memory_files"
codesign --force --deep --sign - "$OUTPUT_DIR/$APP_NAME.app"
printf '\nBuilt: %s/%s.app with %s/memory_files\n' "$OUTPUT_DIR" "$APP_NAME" "$OUTPUT_DIR"
printf 'Run:   open %s/%s.app\n' "$OUTPUT_DIR" "$APP_NAME"
