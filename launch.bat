@echo off
setlocal enabledelayedexpansion

REM Définir le chemin de l'application
set "APP_PATH=%~dp0"
set "SRC_PATH=%APP_PATH%src"

echo Application path: %APP_PATH%
echo Source path: %SRC_PATH%

REM Trouver Python
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON=python"
) else (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON=py -3"
    ) else (
        echo Python n'est pas installe. Installation automatique...
        call :install_python
        if errorlevel 1 (
            echo Echec de l'installation automatique de Python
            echo Veuillez installer Python manuellement depuis https://www.python.org/downloads/
            pause
            exit /b 1
        )
        set "PYTHON=python"
    )
)

echo Python trouve: %PYTHON%

REM Installation des dependances
echo Installation des packages necessaires...
%PYTHON% -m pip install --user --upgrade pip

echo.
echo Version de pip:
%PYTHON% -m pip --version

echo.
echo Installation de wheel et setuptools...
%PYTHON% -m pip install --user --upgrade wheel setuptools

echo.
echo Installation des dependances principales...
%PYTHON% -m pip install --user PyQt5==5.15.9 reportlab==4.0.7 svglib==1.5.1

echo.
echo Details de l'installation PyQt5:
%PYTHON% -m pip show PyQt5

REM Verifier l'installation de PyQt5
echo.
echo Verification de PyQt5...
%PYTHON% -c "import sys; print('Python:', sys.version); import PyQt5; from PyQt5 import QtCore; print('PyQt5:', PyQt5.QtCore.QT_VERSION_STR)"
if errorlevel 1 (
    echo.
    echo Erreur: PyQt5 n'est pas installe correctement
    echo.
    echo Information sur l'environnement Python:
    %PYTHON% -c "import sys; print('Python executable:', sys.executable); print('Python path:', sys.path); print('Pip location:', sys.__pipe_location__ if hasattr(sys, '__pipe_location__') else 'unknown')"
    pause
    exit /b 1
)

REM Lancer l'application
echo.
echo Lancement de l'application...
cd /d "%SRC_PATH%"
%PYTHON% -u main.py
if errorlevel 1 (
    echo.
    echo Erreur lors du lancement de l'application
    echo Code d'erreur: %errorlevel%
    pause
    exit /b 1
)

pause

:install_python
echo.
echo ========================================
echo INSTALLATION AUTOMATIQUE DE PYTHON
echo ========================================
echo.

REM Creer dossier temporaire
set "TEMP_DIR=%TEMP%\roadbook_python_install"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

REM Telecharger Python
echo Telechargement de Python 3.11...
set "PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
set "PYTHON_INSTALLER=%TEMP_DIR%\python-installer.exe"

REM Utiliser PowerShell pour telecharger
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'}"
if errorlevel 1 (
    echo Echec du telechargement de Python
    exit /b 1
)

echo Telechargement termine. Installation en cours...
echo.

REM Installer Python silencieusement avec PATH
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_doc=0
if errorlevel 1 (
    echo Echec de l'installation de Python
    exit /b 1
)

echo Installation de Python terminee.
echo.

REM Nettoyer
if exist "%PYTHON_INSTALLER%" del "%PYTHON_INSTALLER%"
if exist "%TEMP_DIR%" rmdir "%TEMP_DIR%"

REM Actualiser les variables d'environnement
echo Actualisation des variables d'environnement...
for /f "skip=2 tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH') do set "USER_PATH=%%B"
for /f "skip=2 tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH') do set "SYSTEM_PATH=%%B"
set "PATH=%SYSTEM_PATH%;%USER_PATH%"

REM Verifier l'installation
echo Verification de l'installation...
where python >nul 2>&1
if errorlevel 1 (
    echo Python installe mais non trouve dans PATH
    echo Redemarrage necessaire
    exit /b 1
)

echo Python installe avec succes !
echo.
exit /b 0
