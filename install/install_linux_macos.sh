#!/usr/bin/env bash
set -e
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
echo "Optionale Pakete:"
echo "python3 -m pip install -r requirements-optional.txt"
