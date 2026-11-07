@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Environnement introuvable. Lancez d'abord install.bat.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" main.py %*
if errorlevel 1 (
    echo.
    echo REVLO Dash s'est termine avec une erreur. Journal : %LOCALAPPDATA%\REVLO Dash\logs\revlo-dash.log
    pause
)
