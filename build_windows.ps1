$ErrorActionPreference = 'Stop'
$AppName = 'CORDHISK-App-v3.0'
$OutputDir = 'executable_win'
$StageDir = '.pyinstaller-dist'
$WorkDir = '.pyinstaller-build'

Remove-Item $OutputDir, $StageDir, $WorkDir, 'dist' -Recurse -Force -ErrorAction SilentlyContinue

python -m PyInstaller --noconfirm --clean --onedir --windowed --name $AppName `
	--distpath $StageDir --workpath $WorkDir --specpath $WorkDir `
	--exclude-module PyQt5 --exclude-module PySide6 --exclude-module PyQt6 --exclude-module tkinter `
	launcher.py

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
Copy-Item (Join-Path (Join-Path $StageDir $AppName) '*') $OutputDir -Recurse -Force
$DataPath = Join-Path $OutputDir 'memory_files'
if (Test-Path $DataPath) { Remove-Item $DataPath -Recurse -Force }
Copy-Item 'memory_files' $DataPath -Recurse
Remove-Item $StageDir, $WorkDir, 'dist' -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Built: $OutputDir\$AppName.exe"
