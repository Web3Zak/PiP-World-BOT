@echo off
echo =====================================
echo Installing dependencies...
echo =====================================

python -m pip install --upgrade pip

pip install playwright httpx

echo.
echo Installing Playwright Chromium...
playwright install chromium

echo.
echo Installation completed.
pause
