@echo off
rem Called by the service: build.bat <tag> <outputDir> <logFile>
rem (set BUILD_ARGS={tag} {output} {log} in .env; ReleaseNote.md is already written into <outputDir>)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_unity.ps1" -BuildVersion "%~1" -OutputDir "%~2" -LogFile "%~3"
exit /b %ERRORLEVEL%
