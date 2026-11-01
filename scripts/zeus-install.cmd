@echo off
rem Zeus-owned local installer (issue #5, flow B). Never runs an upstream installer.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0zeus-install.ps1" %*
exit /b %ERRORLEVEL%
