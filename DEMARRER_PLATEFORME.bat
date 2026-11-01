@echo off
title Electron Medical Algerie - Serveur Reseau et Base SQLite
color 0A

echo ========================================================================
echo    ELECTRON MEDICAL ALGERIE -- PLATEFORME TECHNICO-COMMERCIAL
echo    Distributeur Officiel Fujifilm Medical Systems
echo    SERVEUR RESEAU LOCAL ET BASE SQLITE MULTI-APPAREILS
echo ========================================================================
echo.

cd /d "d:\TECHNICO-COMMERCIAL"

REM 1. Fermer tout ancien processus sur le port 8085
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr :8085 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM 2. Detection du moteur Python
set "PY_CMD="

if exist "C:\Program Files\dotnet\packs\Microsoft.NET.Runtime.Emscripten.3.1.56.Python.win-x64\10.0.9\tools\python.exe" (
    set "PY_CMD=C:\Program Files\dotnet\packs\Microsoft.NET.Runtime.Emscripten.3.1.56.Python.win-x64\10.0.9\tools\python.exe"
    goto RUN
)

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto RUN
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto RUN
)

for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%d\python.exe" (
        set "PY_CMD=%%d\python.exe"
        goto RUN
    )
)

:RUN
if not defined PY_CMD (
    echo [ATTENTION] Moteur Python non detecte.
    echo Ouverture directe de la plateforme en mode local...
    start "" "d:\TECHNICO-COMMERCIAL\login.html"
    pause
    exit /b
)

echo [OK] Moteur Python connecte : "%PY_CMD%"
echo [OK] Base SQLite : "d:\TECHNICO-COMMERCIAL\technico_commercial.db"
echo [OK] Port reseau : 8085
echo.

REM 3. Ouverture automatique du navigateur dans 2 secondes
start "" cmd /c "timeout /t 2 >nul & start http://localhost:8085/login.html"

REM 4. Lancement du serveur Python SQLite (affiche les adresses IP pour tablettes)
"%PY_CMD%" server.py

pause
