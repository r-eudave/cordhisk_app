$ErrorActionPreference = 'Stop'
$AppName = 'CORDHISK-App-v3.0'
$OutputDir = 'CORDHISK_App_v3_Win'
$StageDir = '.pyinstaller-dist'
$WorkDir = '.pyinstaller-build'
$PythonBin = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { 'python' }

Remove-Item $OutputDir, $StageDir, $WorkDir, 'dist' -Recurse -Force -ErrorAction SilentlyContinue

& $PythonBin -m PyInstaller --noconfirm --clean --onedir --windowed --name $AppName `
	--distpath $StageDir --workpath $WorkDir --specpath $WorkDir `
	--exclude-module PyQt5 --exclude-module PySide6 --exclude-module PyQt6 --exclude-module tkinter `
	launcher.py

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
Copy-Item (Join-Path (Join-Path $StageDir $AppName) '*') $OutputDir -Recurse -Force
$DataPath = Join-Path $OutputDir 'memory_files'
if (Test-Path $DataPath) { Remove-Item $DataPath -Recurse -Force }
New-Item -ItemType Directory -Path $DataPath -Force | Out-Null
Remove-Item $StageDir, $WorkDir, 'dist' -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Built: $OutputDir\$AppName.exe"
