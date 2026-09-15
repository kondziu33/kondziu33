$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw 'Python Launcher (py) not found. Install Python 3.11+ from python.org.' }

py -3 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

if (Test-Path build) { Remove-Item build -Recurse -Force }
if (Test-Path dist) { Remove-Item dist -Recurse -Force }

& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean VOIDRUNNER.spec
Write-Host "BUILD COMPLETE: $PWD\dist\MyGame.exe"
