@echo off
echo Starting Multi-Phone Mirror System
echo.

REM Get master device (first argument)
set MASTER=%1
set SLAVES=%2

if "%MASTER%"=="" (
    echo Usage: scrcpy_mirror.bat MASTER_DEVICE SLAVE_DEVICES
    echo Example: scrcpy_mirror.bat 192.168.1.100:5555 192.168.1.101:5555,192.168.1.102:5555
    pause
    exit
)

echo Master: %MASTER%
echo Slaves: %SLAVES%
echo.

REM Start scrcpy for master
echo Starting screen mirror for master...
start "Master Phone" scrcpy -s %MASTER% --window-title "MASTER - Control Here" --stay-awake --turn-screen-off

timeout /t 2 /nobreak >nul

echo.
echo Master screen is now visible.
echo Starting input mirroring script...
echo.

REM Start Python script to mirror inputs
py input_mirror_auto.py %MASTER% %SLAVES%

pause


