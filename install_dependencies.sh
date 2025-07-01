#!/bin/bash
set -e

echo "Installing system dependencies..."
sudo apt update
sudo apt install -y v4l-utils

v4l2-ctl --list-devices

echo "System dependencies installed."

pip install -r requirements.txt
