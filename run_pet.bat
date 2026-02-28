@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo Виртуальное окружение не найдено. Запусти сначала install_and_run.bat
    pause
    exit /b 1
)

python FixPet\main.py
pause
