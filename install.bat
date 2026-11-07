@echo off
setlocal
cd /d "%~dp0"
title REVLO Dash - Installation
echo ============================================
echo  REVLO Dash - Installation des dependances
echo ============================================
echo.

set "PYCMD="
for %%V in (3.13 3.12 3.11 3.10 3.9) do (
    if not defined PYCMD (
        py -%%V -c "import sys" >nul 2>&1 && set "PYCMD=py -%%V"
    )
)
if not defined PYCMD (
    python -c "import sys; sys.exit(0 if (3,9) <= sys.version_info[:2] <= (3,13) else 1)" >nul 2>&1 && set "PYCMD=python"
)
if not defined PYCMD (
    echo [ERREUR] Python 3.9 a 3.13 ^(64 bits^) est introuvable.
    echo Installez Python 3.12 depuis https://www.python.org/downloads/
    echo et cochez "Add python.exe to PATH", puis relancez install.bat.
    goto :error
)
echo Python utilise : %PYCMD%
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Creation de l'environnement virtuel .venv ...
    %PYCMD% -m venv .venv
    if errorlevel 1 goto :error
)

echo Mise a jour de pip ...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error

echo Installation de PySide6 et PyInstaller ...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Installation terminee. Lancez run.bat pour tester, build.bat pour creer l'EXE.
pause
exit /b 0

:error
echo.
echo L'installation a echoue. Consultez les messages ci-dessus.
pause
exit /b 1
