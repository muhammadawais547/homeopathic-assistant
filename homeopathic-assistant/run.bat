@echo off
REM Homeopathic Assistant Launcher
title Homeopathic Assistant

echo ========================================
echo    Homeopathic Assistant
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher and ensure it is added to your PATH.
    pause
    exit /b 1
)

REM Check if dependencies are installed (simple check)
python -c "import mysql.connector, PyQt6" 2>nul
if errorlevel 1 (
    echo.
    echo Required packages are missing.
    echo Please install them by running:
    echo    pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Starting application...
echo.

REM Run the main application
python main.py

echo.
echo Application closed.
pause