#!/usr/bin/env bash
set -e
cd ~/Obsidian/SecondBrain-Agent
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 scripts/validate_config.py
python3 scripts/production_gate.py
