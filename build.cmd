@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Paji build

set "PY=%~dp0.buildenv\Scripts\python.exe"
set "APPNAME=Paji v1.8.7"
set "NEUTRAL=%~dp0.buildtmp"

if exist "%PY%" goto deps

echo [1/7] creating build venv ...
where python >nul 2>nul
if errorlevel 1 (
    py -3 -m venv .buildenv
) else (
    python -m venv .buildenv
)
if not exist "%PY%" (
    echo.
    echo [!] Could not create .buildenv - is Python 3 installed and on PATH?
    pause
    exit /b 1
)

:deps
echo [2/7] installing PyInstaller + Pillow ...
"%PY%" -m pip install --disable-pip-version-check -q pyinstaller pillow
if errorlevel 1 goto fail

echo [3/7] fetching emoji assets ...
"%PY%" tools\tools_fetch_emoji.py
if errorlevel 1 goto fail

echo [4/7] building thumbnail atlas ...
"%PY%" tools\tools_build_thumbs.py
if errorlevel 1 goto fail

echo [5/7] staging sources into .buildtmp ...
if exist "%NEUTRAL%" rmdir /s /q "%NEUTRAL%"
mkdir "%NEUTRAL%"
copy /y paji.py "%NEUTRAL%" >nul
copy /y emoji_list.py "%NEUTRAL%" >nul
copy /y icon.ico "%NEUTRAL%" >nul
copy /y Paji.spec "%NEUTRAL%" >nul
xcopy /e /i /q assets "%NEUTRAL%\assets" >nul

echo [6/7] building %APPNAME% ...
pushd "%NEUTRAL%"
"%PY%" -m PyInstaller --noconfirm --clean "Paji.spec"
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" goto fail

if not exist "%NEUTRAL%\dist\%APPNAME%.exe" goto fail
if not exist "dist" mkdir "dist"
copy /y "%NEUTRAL%\dist\%APPNAME%.exe" "dist\%APPNAME%.exe" >nul
rmdir /s /q "%NEUTRAL%"

echo [7/8] archiving every build into releases\ ...
"%PY%" tools\tools_archive.py
if errorlevel 1 goto fail

echo [8/8] snapshotting sources into versions\ ...
"%PY%" tools\tools_snapshot.py
if errorlevel 1 goto fail

echo.
echo ============================================
echo  Done: dist\%APPNAME%.exe
echo  Archived: releases\  (all versions kept)
echo  Snapshot: versions\  (all sources kept)
echo ============================================
echo.
pause
exit /b 0

:fail
echo.
echo [!] BUILD FAILED - see the messages above.
echo.
if exist "%NEUTRAL%" rmdir /s /q "%NEUTRAL%"
pause
exit /b 1
