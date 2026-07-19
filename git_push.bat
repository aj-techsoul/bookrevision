@echo off
echo ===================================================
echo   Initializing Git and Pushing to GitHub
echo ===================================================
echo.

:: Navigate to script directory
cd /d "%~dp0"

:: Check if git is installed
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed or not in PATH.
    echo Please install Git and try again.
    pause
    exit /b 1
)

:: Initialize git repository
if not exist .git (
    echo [1/6] Initializing local Git repository...
    git init
) else (
    echo [1/6] Git repository already initialized.
)

:: Configure local git user settings if not set globally to prevent commit failures
git config --global user.email >nul 2>nul
if %errorlevel% neq 0 (
    echo [2/6] Setting local git user config for this repository...
    git config --local user.name "aj-techsoul"
    git config --local user.email "aj-techsoul@users.noreply.github.com"
) else (
    echo [2/6] Git user configuration already exists.
)

:: Add remote origin if not already added
git remote | findstr /x /c:"origin" >nul
if %errorlevel% neq 0 (
    echo [3/6] Adding remote origin...
    git remote add origin https://github.com/aj-techsoul/bookrevision.git
) else (
    echo [3/6] Remote origin already exists.
    git remote set-url origin https://github.com/aj-techsoul/bookrevision.git
)

:: Fetch remote branches
echo [4/6] Fetching from remote repository...
git fetch origin

:: Pull remote main branch to get remote files (like LICENSE)
echo [5/6] Pulling main branch from remote...
git checkout -b main 2>nul
if %errorlevel% neq 0 (
    git checkout main
)
git pull origin main --allow-unrelated-histories

:: Stage all local files
echo [6/6] Staging project files...
git add .

:: Commit files
echo [7/7] Committing files...
git commit -m "Initial commit of bookrevision project"

:: Push to remote main branch
echo.
echo ===================================================
echo   Pushing to GitHub...
echo ===================================================
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Project successfully pushed to GitHub!
) else (
    echo.
    echo [ERROR] Push failed. If this is an authentication/permission issue,
    echo please make sure you are logged in to GitHub on your machine.
)

pause
