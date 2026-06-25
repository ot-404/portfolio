@echo off
REM One-click deploy: rebuilds the static site and publishes it to GitHub Pages.
REM Double-click this file, or run it from a terminal.
cd /d "%~dp0"

echo === Building static site ===
".venv\Scripts\python.exe" build_static.py
if errorlevel 1 (
    echo.
    echo Build FAILED - see the errors above. Nothing was deployed.
    pause
    exit /b 1
)

echo.
echo === Publishing to GitHub Pages ===
cd build
git init -q
git add -A
git -c user.name="ripp3" -c user.email="poraise29@gmail.com" commit -q -m "Deploy portfolio (static build)"
git branch -M main
git remote remove origin 2>nul
git remote add origin https://github.com/ot-404/ot-404.github.io.git
git push -q -u origin main --force
if errorlevel 1 (
    echo.
    echo Push FAILED - check your internet/GitHub sign-in and try again.
    pause
    exit /b 1
)

echo.
echo Done! Live at https://ot-404.github.io
echo (Allow ~1 minute for GitHub Pages to rebuild.)
pause
