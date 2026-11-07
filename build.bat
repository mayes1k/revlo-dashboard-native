@echo off
setlocal
cd /d "%~dp0"
title REVLO Dash - Compilation
if not exist ".venv\Scripts\python.exe" (
    echo Environnement introuvable. Lancez d'abord install.bat.
    pause
    exit /b 1
)
if not exist "assets\revlo-logo.ico" (
    echo Fichier assets\revlo-logo.ico introuvable.
    pause
    exit /b 1
)

echo Nettoyage ...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Compilation de REVLO Dash.exe ^(plusieurs minutes^) ...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name "REVLO Dash" ^
    --icon "assets\revlo-logo.ico" ^
    --add-data "assets;assets" ^
    --add-data "revlo-logo.svg;." ^
    main.py
if errorlevel 1 (
    echo.
    echo La compilation a echoue.
    pause
    exit /b 1
)

if exist "REVLO Dash.spec" del "REVLO Dash.spec"
echo.
echo ============================================
echo  Termine : dist\REVLO Dash.exe
echo ============================================
explorer dist
pause
