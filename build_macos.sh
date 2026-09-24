#!/bin/sh
set -eu

APP_NAME="CORDHISK-App-v3.0"
PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" -m PyInstaller --noconfirm --clean --onedir --windowed --name "$APP_NAME" \
	--exclude-module PyQt5 --exclude-module PySide6 --exclude-module PyQt6 --exclude-module tkinter \
	launcher.py
rm -rf "dist/memory_files"
cp -R memory_files "dist/memory_files"
printf '\nBuilt: dist/%s.app with dist/memory_files\n' "$APP_NAME"
printf 'Run:   open dist/%s.app\n' "$APP_NAME"
