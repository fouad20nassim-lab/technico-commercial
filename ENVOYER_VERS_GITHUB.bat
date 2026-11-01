@echo off
title Mise a jour Technico-Commercial vers GitHub
cd /d "D:\TECHNICO-COMMERCIAL"

echo ======================================================================
echo    ENVOI ET MISE A JOUR VERS GITHUB & RENDER
echo ======================================================================
echo.
git add .
git commit -m "Mise a jour Technico-Commercial (%DATE% %TIME%)"
git push origin main
echo.
echo ======================================================================
echo   SUCCES ! Vos modifications sont en ligne.
echo ======================================================================
pause
