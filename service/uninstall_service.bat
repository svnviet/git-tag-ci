@echo off
rem Removes the git-tag-ci service. Run as Administrator.
setlocal
set NSSM=nssm
if exist "%~dp0nssm.exe" set NSSM="%~dp0nssm.exe"
net session >nul 2>&1
if errorlevel 1 (echo [ERROR] Please run as Administrator. & exit /b 1)
%NSSM% stop git-tag-ci
%NSSM% remove git-tag-ci confirm
endlocal
