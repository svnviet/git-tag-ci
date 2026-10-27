@echo off
rem Runs the service. Configure the environment variables below.
set REPO_URL=https://github.com/owner/repo.git
set WORK_DIR=D:\Work\MeterProject
set BUILD_SCRIPT=%~dp0examples\build.bat
set TAG_PREFIXES=U_Master_GUI
set TAG_PARAM_SEP=_
set OUTPUT_DIR=D:\Work\Output
rem build.bat <tag> <outputDir> <releaseNotes>
set BUILD_ARGS={tag} {output} {notes}
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set PY=.venv\Scripts\python.exe) else (set PY=python)
%PY% -m uvicorn app.main:app --host 0.0.0.0 --port 8000
