@echo off
chcp 65001 >nul
REM Model bhi ISI folder ke andar rahega — folder copy = poora Superhero portable
if not exist "%~dp0models" mkdir "%~dp0models" >nul 2>&1
set "OLLAMA_MODELS=%~dp0models"
title Superhero
cd /d %~dp0

REM ============================================================
REM   SUPERHERO — EK HI DARWAZA
REM   Double-click = dimaag check/serve khud + premium UI browser me.
REM   Dimaag LOCAL hai: Unlimited - No Token - Offline.
REM ============================================================

REM --- Superhero pehle se chal raha hai to sirf browser kholo ---
curl.exe -s http://127.0.0.1:8765/health >nul 2>&1
if %errorlevel%==0 (
  start "" http://127.0.0.1:8765
  exit
)

REM --- 1) Dimaag ka engine dhoondo ---
set "OLLAMA_EXE="
where ollama >nul 2>&1
if %errorlevel%==0 set "OLLAMA_EXE=ollama"
if not defined OLLAMA_EXE if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
if not defined OLLAMA_EXE if exist "%ProgramFiles%\Ollama\ollama.exe" set "OLLAMA_EXE=%ProgramFiles%\Ollama\ollama.exe"
if not defined OLLAMA_EXE (
  echo.
  echo   Superhero ka dimaag is laptop par laga hi nahi hai.
  echo   Pehle EK BAAR Dimaag-Lagao.bat par double-click karo —
  echo   woh dimaag khud laga dega. Phir yehi file chalana.
  echo.
  pause
  exit /b 1
)

REM --- 2) Dimaag so raha ho to khud jaga do ---
curl.exe -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
  start "" /min "%OLLAMA_EXE%" serve
  timeout /t 3 /nobreak >nul
)

REM --- 3) Dimaag taiyaar na ho to khud download karo (sirf pehli baar) ---
"%OLLAMA_EXE%" list | findstr /I "qwen2.5" >nul 2>&1
if errorlevel 1 (
  echo.
  echo   Superhero ka dimaag (takreeban 2 GB) aa raha hai...
  echo   Progress neeche dikhegi. Ye sirf pehli baar hota hai.
  echo.
  "%OLLAMA_EXE%" pull qwen2.5:3b
)

REM --- 4) Superhero ka premium UI (web) chalu karo ---
where pyw >nul 2>&1
if %errorlevel%==0 (
  start "" /min pyw superhero_web.py
  goto :open
)
where pythonw >nul 2>&1
if %errorlevel%==0 (
  start "" /min pythonw superhero_web.py
  goto :open
)
where py >nul 2>&1
if %errorlevel%==0 (
  start "" /min py superhero_web.py
  goto :open
)
start "" /min python superhero_web.py

:open
timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:8765
exit
