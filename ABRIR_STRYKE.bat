@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title STRYKE Launcher
set PORT=8765

echo [STRYKE] Encerrando servidor antigo, se existir...
taskkill /FI "WINDOWTITLE eq STRYKE Server" /T /F >nul 2>nul
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do taskkill /PID %%P /F >nul 2>nul

timeout /t 1 /nobreak >nul
where py >nul 2>nul
if %errorlevel%==0 (
    start "STRYKE Server" /min cmd /k "title STRYKE Server && cd /d ""%~dp0"" && py -m http.server %PORT%"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        start "STRYKE Server" /min cmd /k "title STRYKE Server && cd /d ""%~dp0"" && python -m http.server %PORT%"
    ) else (
        echo Python nao foi encontrado.
        pause
        exit /b 1
    )
)
timeout /t 2 /nobreak >nul
start "" "http://localhost:%PORT%/?v=39"
exit /b 0
