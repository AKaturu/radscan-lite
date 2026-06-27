@echo off
REM --------------------------------------------------
REM RadScan Lite — GitHub Upload Helper
REM --------------------------------------------------
REM 1. Create your repo on github.com (empty, no README)
REM 2. Edit the URL below, then run this script.
REM --------------------------------------------------

set REPO_URL=https://github.com/YOUR_USERNAME/radscan-lite.git

echo.
echo Step 1: Add remote origin
git remote add origin %REPO_URL%

echo.
echo Step 2: Push to GitHub
git push -u origin master

echo.
echo Done! Visit: https://github.com/YOUR_USERNAME/radscan-lite
pause
