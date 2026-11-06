@echo off
chcp 65001 >nul
REM Model isi folder ke andar aayega — portable Superhero ke liye
if not exist "%~dp0models" mkdir "%~dp0models" >nul 2>&1
set "OLLAMA_MODELS=%~dp0models"
title Superhero - Dimaag lagaya ja raha hai
cd /d %~dp0
echo.
echo ============================================================
echo   SUPERHERO - OLLAMA SETUP (ek baar hi karna hai)
echo   Ye khidki khud sab karegi. Beech me band mat karna.
echo ============================================================
echo.

REM --- 1) Pehle se laga hai to dobara install nahi ---
where ollama >nul 2>&1
if %errorlevel%==0 goto :model
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" goto :model_path
if exist "%ProgramFiles%\Ollama\ollama.exe" goto :model_path

echo [1/3] Superhero ke dimaag ka engine download ho raha hai...
echo       (official pate se, takreeban 1 GB, thoda samay lagega)
curl.exe -L --fail -o EngineSetup.exe https://ollama.com/download/OllamaSetup.exe
if not exist EngineSetup.exe (
  echo.
  echo Download nahi ho paya. Internet check karo aur is file ko dobara chalao.
  pause
  exit /b 1
)
echo.
echo [2/3] Engine chup-chaap install ho raha hai...
start /wait EngineSetup.exe /S
del EngineSetup.exe >nul 2>&1
REM PATH isi session me taza karo taaki engine abhi mil jaye
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Ollama;%ProgramFiles%\Ollama"
where ollama >nul 2>&1
if %errorlevel% neq 0 (
  echo.
  echo Install ke baad bhi engine nahi mila. Laptop ko ek baar restart karke
  echo is file ko dobara chalao - model wahi se aage badhega.
  pause
  exit /b 1
)
goto :model

:model_path
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Ollama;%ProgramFiles%\Ollama"
echo Engine pehle se laga hua hai - dobara install nahi kiya.
goto :model

:model
echo.
echo [3/3] Superhero ka dimaag (takreeban 2 GB) download ho raha hai...
echo       Progress neeche dikhegi. Khatm hone tak intezaar karo.
ollama serve >nul 2>&1 &
timeout /t 3 /nobreak >nul
ollama pull qwen2.5:3b
if %errorlevel% neq 0 (
  echo.
  echo Model download pura nahi hua. Internet dekh kar is file ko dobara chalao -
  echo download wahi se aage badhega, shuru se nahi.
  pause
  exit /b 1
)
echo.
echo ============================================================
echo   HO GAYA! Superhero ka dimaag taiyaar hai.
echo   Ab is khidki ko band karo aur Superhero-App.bat chalao.
echo   Uske baad roz sirf Superhero-App.bat hi chalana hai.
echo ============================================================
echo.
pause
