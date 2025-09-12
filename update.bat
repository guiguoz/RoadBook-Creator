@echo off
setlocal enabledelayedexpansion

echo ========================================
echo     MISE A JOUR ROADBOOK EDITOR
echo ========================================
echo.

REM URL de téléchargement (à modifier selon votre hébergement)
set "UPDATE_URL=https://github.com/username/roadbook-app/releases/latest/download/roadbook_app.zip"
set "TEMP_DIR=%TEMP%\roadbook_update"
set "UPDATE_FILE=%TEMP_DIR%\roadbook_update.zip"

REM Créer dossier temporaire
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

echo Téléchargement de la mise à jour...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%UPDATE_URL%' -OutFile '%UPDATE_FILE%'}"

if errorlevel 1 (
    echo Échec du téléchargement
    pause
    exit /b 1
)

echo Extraction de la mise à jour...
powershell -Command "Expand-Archive -Path '%UPDATE_FILE%' -DestinationPath '%TEMP_DIR%' -Force"

echo Application de la mise à jour...
REM Sauvegarder les projets utilisateur
if exist "projects" xcopy "projects" "%TEMP_DIR%\backup_projects" /E /I /Y

REM Copier les nouveaux fichiers
xcopy "%TEMP_DIR%\roadbook_app\*" "." /E /Y

REM Restaurer les projets
if exist "%TEMP_DIR%\backup_projects" (
    if not exist "projects" mkdir "projects"
    xcopy "%TEMP_DIR%\backup_projects\*" "projects" /E /Y
)

REM Nettoyer
rmdir /S /Q "%TEMP_DIR%"

echo.
echo Mise à jour terminée avec succès !
echo Vous pouvez maintenant relancer l'application.
echo.
pause