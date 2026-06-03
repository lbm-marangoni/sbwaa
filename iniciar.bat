@echo off
setlocal

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

:: 1. Obsidian
start "" "%LOCALAPPDATA%\Programs\Obsidian\Obsidian.exe"
timeout /t 2 /nobreak >nul

:: 2. VS Code (Claude Code abre automaticamente pelo task folderOpen)
start "" code "%ROOT%"
timeout /t 1 /nobreak >nul

:: 3. Verificar fila de teses (tray notification se houver COMPRAR)
start "" pythonw "%ROOT%\scripts\automation\startup_check.py"
timeout /t 1 /nobreak >nul

:: 4. Painel SBWAA
start "" pythonw "%ROOT%\interface\ui.py"

endlocal
