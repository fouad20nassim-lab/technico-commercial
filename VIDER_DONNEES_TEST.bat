@echo off
title Remise a Zero de la Base SQLite Technico-Commercial
cd /d "D:\TECHNICO-COMMERCIAL"

echo ======================================================================
echo   REMISE A ZERO DE L'APPLICATION (VIDER LES DONNEES DE TEST)
echo ======================================================================
echo.
echo Cette action va effacer :
echo   - Tous les rapports de test (visites, inspections, installations, formations)
echo   - Tous les clients et equipements de test
echo   - Toutes les echeances de revision sous garantie
echo.
echo Vos comptes utilisateurs (admin, techniciens) et reglages sont CONSERVES !
echo.
set /p CONFIRM=Tapez OUI pour confirmer la remise a zero : 
if /i not "%CONFIRM%"=="OUI" (
    echo.
    echo Operation annulee. Rien n'a ete modifie.
    pause
    exit /b
)

python -c "import sqlite3, shutil, datetime, os; os.makedirs('backups', exist_ok=True); bk = f'backups/manuel_avant_purge_{datetime.datetime.now().strftime(\"%%Y%%m%%d_%%H%%M%%S\")}.db'; shutil.copy2('technico_commercial.db', bk) if os.path.exists('technico_commercial.db') else None; conn = sqlite3.connect('technico_commercial.db'); c = conn.cursor(); c.execute('DELETE FROM rapports'); c.execute('DELETE FROM garanties_revisions'); c.execute('DELETE FROM clients'); c.execute('DELETE FROM equipements'); conn.commit(); conn.execute('VACUUM'); conn.close(); print('Succes : Base SQLite remise a neuf !')"

echo.
echo ======================================================================
echo   TERMINE ! L'application est prete pour vos technico-commerciaux.
echo ======================================================================
echo.
pause

