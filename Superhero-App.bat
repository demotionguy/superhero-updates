@echo off
title Superhero
cd /d %~dp0
REM Model isi folder ke andar — portable
if not exist "%~dp0models" mkdir "%~dp0models" >nul 2>&1
set "OLLAMA_MODELS=%~dp0models"
REM Agar dimaag ka engine laga hai lekin so raha hai, to pehle wahi chalu karo
REM taaki app khulte hi "dimaag band hai" wala error na aaye.
set "OLLAMA_EXE="
where ollama >nul 2>&1
if %errorlevel%==0 set "OLLAMA_EXE=ollama"
if not defined OLLAMA_EXE if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
if not defined OLLAMA_EXE if exist "%ProgramFiles%\Ollama\ollama.exe" set "OLLAMA_EXE=%ProgramFiles%\Ollama\ollama.exe"
if defined OLLAMA_EXE (
  curl.exe -s http://localhost:11434/api/tags >nul 2>&1
  if errorlevel 1 (
    start "" /min "%OLLAMA_EXE%" serve
    timeout /t 2 /nobreak >nul
  )
)
REM Superhero ki app-khidki bina kaali terminal ke kholne ke 3 tareeke,
REM jo pehle mile wahi chalega. Kaunsa chala, launcher-log.txt me likh jata hai.
where pyw >nul 2>&1
if %errorlevel%==0 (
  echo pyw se khula > launcher-log.txt
  start "" pyw superhero_app.py
  exit
)
where pythonw >nul 2>&1
if %errorlevel%==0 (
  echo pythonw se khula > launcher-log.txt
  start "" pythonw superhero_app.py
  exit
)
where py >nul 2>&1
if %errorlevel%==0 (
  echo py -w se khula > launcher-log.txt
  start "" py -w superhero_app.py
  exit
)
echo SIRF python mila - kaali khidki ke saath khulega > launcher-log.txt
start "" python superhero_app.py
