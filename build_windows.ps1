$ErrorActionPreference = 'Stop'
$AppName = 'CORDHISK-App-v3.0'

python -m PyInstaller --noconfirm --clean --onedir --windowed --name $AppName `
	--exclude-module PyQt5 --exclude-module PySide6 --exclude-module PyQt6 --exclude-module tkinter `
	launcher.py
$DataPath = Join-Path "dist\$AppName" 'memory_files'
if (Test-Path $DataPath) { Remove-Item $DataPath -Recurse -Force }
Copy-Item 'memory_files' $DataPath -Recurse
Write-Host "Built: dist\$AppName\$AppName.exe"
