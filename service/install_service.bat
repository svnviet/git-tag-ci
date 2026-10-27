@echo off
rem Installs git-tag-ci as a Windows service (starts with Windows). Run as Administrator.
rem Requires nssm.exe in PATH or next to this file (https://nssm.cc/download).
rem
rem Usage:
rem   install_service.bat                       -> runs as LocalSystem
rem   install_service.bat .\username password   -> runs as your account (RECOMMENDED)
rem
rem Prefer your own account: a LocalSystem service has no git credentials / Unity license of the user.
setlocal
set SVC=git-tag-ci
set ROOT=%~dp0..

net session >nul 2>&1
if errorlevel 1 (echo [ERROR] Please run as Administrator. & exit /b 1)

set NSSM=nssm
if exist "%~dp0nssm.exe" set NSSM="%~dp0nssm.exe"
%NSSM% version >nul 2>&1
if errorlevel 1 (echo [ERROR] nssm.exe not found. Download it from https://nssm.cc/download and put it in PATH or in the service\ folder. & exit /b 1)

if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"

%NSSM% install %SVC% "%ComSpec%" /c "\"%ROOT%\run.bat\""
%NSSM% set %SVC% AppDirectory "%ROOT%"
%NSSM% set %SVC% DisplayName "Git Tag CI"
%NSSM% set %SVC% Description "Watches git tags and builds when a new tag appears"
%NSSM% set %SVC% Start SERVICE_AUTO_START
%NSSM% set %SVC% AppStdout "%ROOT%\logs\service.out.log"
%NSSM% set %SVC% AppStderr "%ROOT%\logs\service.err.log"
%NSSM% set %SVC% AppRotateFiles 1
%NSSM% set %SVC% AppRotateBytes 10485760
%NSSM% set %SVC% AppExit Default Restart
%NSSM% set %SVC% AppRestartDelay 5000
if not "%~1"=="" %NSSM% set %SVC% ObjectName "%~1" "%~2"

%NSSM% start %SVC%
echo.
echo Service "%SVC%" installed and started. API: http://localhost:8000/docs
endlocal
