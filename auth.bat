@echo off
cd /d "%~dp0"
where python >nul 2>&1 && python "%~dp0auth.py" %* && exit /b %ERRORLEVEL%
where py >nul 2>&1 && py "%~dp0auth.py" %* && exit /b %ERRORLEVEL%
echo Python was not found. Install from https://www.python.org/downloads/ and ensure "Add python.exe to PATH" is checked.
exit /b 1
