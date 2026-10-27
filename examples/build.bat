@echo off
rem Called by the service: build.bat <tag> <outputDir> <releaseNotesFile>
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_unity.ps1" -BuildVersion "%~1" -OutputDir "%~2" -ReleaseNotes "%~3"
exit /b %ERRORLEVEL%
