@echo off
taskkill /FI "WINDOWTITLE eq STRYKE Server" /T /F >nul 2>nul
echo Servidor STRYKE encerrado.
timeout /t 1 /nobreak >nul
