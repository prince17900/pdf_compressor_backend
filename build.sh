#!/usr/bin/env bash
# This script will install dependencies for the Python app and system packages.

# Exit immediately if a command exits with a non-zero status.
set -o errexit

echo "--- Starting build process ---"

# 1. Install Python dependencies from requirements.txt
echo "--- Installing Python packages ---"
pip install -r requirements.txt

# 2. Install system dependencies (Ghostscript)
# We use -y to confirm installation and --no-install-recommends to keep the image slim.
echo "--- Installing Ghostscript ---"
apt-get update -y
apt-get install -y --no-install-recommends ghostscript

echo "--- Build process finished successfully ---"
