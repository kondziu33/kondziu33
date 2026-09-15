@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo VOIDRUNNER - Windows Build
echo ============================================

where py >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python Launcher ^(py^) not found.
  echo Install Python 3.12+ from python.org and enable the launcher.
  exit /b 1
)

py -3 -m venv .venv
if errorlevel 1 exit /b 1
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python -m PyInstaller --noconfirm --clean VOIDRUNNER.spec
if errorlevel 1 (
  echo BUILD FAILED.
  exit /b 1
)

echo.
echo BUILD COMPLETE:
echo %CD%\dist\MyGame.exe
endlocal
