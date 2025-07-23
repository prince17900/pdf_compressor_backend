#!/usr/bin/env bash
# exit on error
set -o errexit

# Install pip dependencies
pip install -r requirements.txt

# Install Ghostscript
apt-get update && apt-get install -y ghostscript