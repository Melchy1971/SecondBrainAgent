@echo off
echo SecondBrain-Agent Installation Windows
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Optionale Pakete installieren?
echo python -m pip install -r requirements-optional.txt
pause
