#!/bin/bash

echo "========================================"
echo "Farm2Market MySQL Setup Script"
echo "========================================"
echo

echo "Checking Python installation..."
python3 --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python3 is not installed or not in PATH"
    exit 1
fi

echo
echo "Installing required Python packages..."
pip3 install djangorestframework django-cors-headers mysql-connector-python

echo
echo "Running MySQL setup..."
python3 setup_mysql.py

echo
echo "Setup complete!"
