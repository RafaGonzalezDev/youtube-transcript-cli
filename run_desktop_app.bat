@echo off
echo YouTube Transcript Downloader - Setup and Launch
echo ================================================
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not found in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b
)
echo Python found successfully.
echo.

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo Error: requirements.txt not found.
    echo Please make sure you have the requirements file in the same directory.
    pause
    exit /b
)

REM Check if required libraries are already installed
echo Checking required Python libraries...
set "NEED_INSTALL=0"
call :check_module youtube_transcript_api || set "NEED_INSTALL=1"
call :check_module requests || set "NEED_INSTALL=1"
call :check_module bs4 || set "NEED_INSTALL=1"

if "%NEED_INSTALL%"=="0" (
    echo All required libraries are already installed.
    echo.
    goto launch_app
)

echo.

REM Show dependencies and ask for confirmation
echo The following Python libraries will be installed:
echo - youtube-transcript-api ^(^>=0.6.0^)
echo - requests ^(^>=2.25.0^)
echo - beautifulsoup4 ^(^>=4.9.0^)
echo.
set /p install_choice="Do you want to install these libraries? (Y/N): "

REM Convert to uppercase for comparison
for %%i in ("%install_choice%") do set "install_choice=%%~i"
if /i "%install_choice%"=="Y" goto install
if /i "%install_choice%"=="YES" goto install
if /i "%install_choice%"=="N" goto skip_install
if /i "%install_choice%"=="NO" goto skip_install

echo Invalid choice. Please enter Y or N.
pause
exit /b

:check_module
python -c "import %~1" >nul 2>&1
if %errorlevel% neq 0 (
    echo Missing: %~1
    exit /b 1
)
exit /b 0

:install
echo.
echo Installing dependencies from requirements.txt...
python -m pip install -r requirements.txt

REM Check if installation was successful
if %errorlevel% neq 0 (
    echo.
    echo Error: Failed to install required libraries.
    echo Please check your Python and pip installation.
    pause
    exit /b
)

echo.
echo All libraries installed successfully!
goto launch_app

:skip_install
echo.
echo Skipping library installation.
echo Note: The application may not work if required libraries are missing.
echo.

:launch_app
echo Starting YouTube Transcript Downloader...
echo.

python desktop_app.py

if %errorlevel% neq 0 (
    echo.
    echo Error: Failed to start the application.
    echo This might be due to missing dependencies or Python issues.
)

pause