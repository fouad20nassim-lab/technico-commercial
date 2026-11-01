@echo off
title Mise a jour Technico-Commercial en Ligne
cd /d "D:\TECHNICO-COMMERCIAL"

echo ======================================================================
echo    SYNCHRONISATION ET MISE A JOUR EN LIGNE (Render + GitHub)
echo ======================================================================
echo.
echo [1/3] Enregistrement de vos modifications...
git add .
git commit -m "Mise a jour de l'application (%DATE% %TIME%)"

echo.
echo [2/3] Envoi vers votre compte GitHub...
git push origin main

echo.
echo ======================================================================
echo   [3/3] REUSSI ! Render met a jour votre site en ligne automatiquement.
echo         Vos nouveautes seront visibles dans 30 a 60 secondes !
echo ======================================================================
echo.
pause
