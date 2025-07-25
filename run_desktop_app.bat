@echo off
echo Checking for required Python libraries...

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo Error: requirements.txt not found.
    echo Please make sure you have the requirements file in the same directory.
    pause
    exit /b
)

REM Install dependencies using pip
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
echo All libraries are installed. Starting YouTube Transcript Downloader...
echo.

python desktop_app.py

pause