Write-Host "SecondBrain-Agent v7 Installation"
Set-Location "H:\SecondBrainAgent\SecondBrain-Agent"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts\validate_config.py
python scripts\production_gate.py
