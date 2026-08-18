@echo off
setlocal enabledelayedexpansion
title NPS Server - check and fix
cd /d "%~dp0"

echo.
echo  ============================================================
echo   NPS SERVER - CHECK AND FIX
echo  ============================================================
echo.
echo  This checks why the game crashes at 97%%, makes the setup
echo  safe, and writes REPORT.txt next to this file.
echo.
echo  Nothing is deleted. Anything it moves is listed in the report.
echo.

REM ---- find a python: the server's own venv first, then the system one ----
set "PY="
for %%P in (
  ".venv\Scripts\python.exe"
  "..\.venv\Scripts\python.exe"
  "..\..\.venv\Scripts\python.exe"
  ".venv-1\Scripts\python.exe"
  "..\.venv-1\Scripts\python.exe"
  "..\..\.venv-1\Scripts\python.exe"
) do (
  if not defined PY if exist "%%~P" set "PY=%%~fP"
)

if not defined PY (
  where py >nul 2>&1 && set "PY=py"
)
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)

if not defined PY (
  echo  Could not find Python on this PC.
  echo.
  echo  You run the server with Python, so it is installed somewhere -
  echo  put this file next to the server's .venv folder and try again,
  echo  or install Python from python.org and rerun.
  echo.
  pause
  exit /b 1
)

echo  Using Python: %PY%
echo.

"%PY%" "%~dp0timemsm_check.py"
set "RC=%ERRORLEVEL%"

echo.
echo  ============================================================
if "%RC%"=="0" (
  echo   Done. Send REPORT.txt back if it still crashes.
) else (
  echo   Finished with problems - see the messages above.
)
echo  ============================================================
echo.
pause
endlocal
