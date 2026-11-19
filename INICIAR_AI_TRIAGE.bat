@echo off
title AI-Triage Hospitalario - UMB
color 0A
cls
echo ======================================================================
echo    AI-Triage: Sistema Inteligente de Clasificacion Clinica (v4.0)
echo    Universidad Manuela Beltran - Ingenieria de Software
echo ======================================================================
echo.
echo  Iniciando aplicacion...
echo.

cd /d "%~dp0"

REM Cerrar cualquier instancia previa
taskkill /f /im "AI-Triage.exe" >nul 2>&1
timeout /t 1 /nobreak >nul

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  [OK] Python detectado. Iniciando servidor en vivo con Google Gemini...
    start "AI-Triage Server" python "%~dp0run_app.py"
    timeout /t 3 /nobreak >nul
    start http://127.0.0.1:8000/
    echo  [OK] Navegador abierto en http://127.0.0.1:8000/
    echo.
    echo  La aplicacion esta corriendo. Puedes cerrar esta ventana.
) else if exist "%~dp0dist\AI-Triage\AI-Triage.exe" (
    echo  [OK] Iniciando ejecutable portable...
    start "" "%~dp0dist\AI-Triage\AI-Triage.exe"
    timeout /t 4 /nobreak >nul
    start http://127.0.0.1:8000/
    echo  [OK] Navegador abierto en http://127.0.0.1:8000/
) else (
    echo  [ERROR] No se encontro Python ni dist\AI-Triage\AI-Triage.exe
    pause
    exit /b 1
)

timeout /t 3 /nobreak >nul
