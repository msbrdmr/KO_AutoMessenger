@echo off
setlocal enabledelayedexpansion

REM Configuration
set "UPDATE_URL=https://github.com/msbrdmr/KO_AutoMessenger/releases/latest/download/dist.zip"
set "DOWNLOAD_FILE=update_temp.zip"
set "EXTRACT_DIR=update_temp"
set "TARGET_DIR=%~dp0"
set "EXE_NAME=knight_chat_bot.exe"

echo -----------------------------------------
echo         KO_AutoMessenger Updater         
echo -----------------------------------------

REM Step 1: Download the update
echo Checking for updates...
if exist "%DOWNLOAD_FILE%" del "%DOWNLOAD_FILE%"
powershell -Command "Invoke-WebRequest -Uri '%UPDATE_URL%' -OutFile '%DOWNLOAD_FILE%'"
if %errorlevel% neq 0 (
    echo Failed to download the update. Exiting...
    pause
    exit /b
)
echo Update downloaded successfully.

REM Step 2: Extract the update
echo Extracting update...
if exist "%EXTRACT_DIR%" rmdir /s /q "%EXTRACT_DIR%"
powershell -Command "Expand-Archive -Force '%DOWNLOAD_FILE%' '%EXTRACT_DIR%'"
if %errorlevel% neq 0 (
    echo Failed to extract the update. Exiting...
    pause
    exit /b
)
echo Update extracted successfully.

REM Step 3: Copy updated files
echo Installing update...
xcopy "%EXTRACT_DIR%\*" "%TARGET_DIR%" /s /e /y
if %errorlevel% neq 0 (
    echo Failed to install the update. Exiting...
    pause
    exit /b
)
echo Update installed successfully.

REM Step 4: Cleanup temporary files
echo Cleaning up...
del "%DOWNLOAD_FILE%"
rmdir /s /q "%EXTRACT_DIR%"

REM Step 5: Launch the application
echo Starting application...
start "" "%TARGET_DIR%%EXE_NAME%"

echo Update complete. Enjoy!
exit
