@echo off
REM === Автоустановка и запуск Desktop Pet ===

REM Переходим в папку скрипта
cd /d "%~dp0"

echo [1/4] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python не найден в PATH.
    echo Установи Python 3.10+ и отметь "Add to PATH" при установке.
    pause
    exit /b 1
)

echo [2/4] Создание виртуального окружения .venv...
if not exist ".venv" (
    python -m venv .venv
) else (
    echo Виртуальное окружение уже существует.
)

echo [3/4] Установка зависимостей...
call ".venv\Scripts\activate.bat"
pip install --upgrade pip
pip install -r requirements.txt

echo [4/4] Запуск питомца...
python FixPet\main.py

echo.
echo Приложение завершено.
pause
