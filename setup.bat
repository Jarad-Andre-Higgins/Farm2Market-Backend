@echo off
echo ========================================
echo Farm2Market MySQL Setup Script
echo ========================================
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo Installing required Python packages...
pip install djangorestframework django-cors-headers mysql-connector-python

echo.
echo Running MySQL setup...
python setup_mysql.py

echo.
echo Setup complete! Press any key to continue...
pause
