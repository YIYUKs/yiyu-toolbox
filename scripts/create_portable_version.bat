@echo off
chcp 65001 >nul
title Yiyu Toolbox - Portable Build

set "CORE_DIR=..\yiyu Toolbox core"
set "PROJ_DIR=..\releases\yiyu_toolbox_portable"
set "EXE_NAME=乙羽的工具箱.exe"

echo [Step 1] Checking output directory...
if not exist "%PROJ_DIR%" (
    echo Creating directory: %PROJ_DIR%
    mkdir "%PROJ_DIR%"
) else (
    echo Directory exists: %PROJ_DIR%
)

echo [Step 2] Checking Python Runtime...
if not exist "%PROJ_DIR%\runtime\Scripts\python.exe" (
    echo Creating venv...
    python -m venv "%PROJ_DIR%\runtime"
) else (
    echo Runtime OK
)

echo [Step 3] Installing dependencies...
"%PROJ_DIR%\runtime\Scripts\pip" install -r "%CORE_DIR%\requirements.txt"

echo [Step 4] Copying files...
xcopy /s /e /y "%CORE_DIR%\src" "%PROJ_DIR%\src\" >nul
xcopy /s /e /y "%CORE_DIR%\resources" "%PROJ_DIR%\resources\" >nul
xcopy /s /e /y "%CORE_DIR%\model" "%PROJ_DIR%\model\" >nul
if not exist "%PROJ_DIR%\runtime\Scripts" mkdir "%PROJ_DIR%\runtime\Scripts"
copy "%CORE_DIR%\*.dll" "%PROJ_DIR%\runtime\Scripts\" /y >nul

echo [Step 5] Compiling EXE...
set "CSC_EXE=C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if not exist "%CSC_EXE%" set "CSC_EXE=C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
if not exist "%CSC_EXE%" (
    echo Fatal Error: csc.exe not found!
    pause
    exit /b 1
)

set "ICON_CMD="
if exist "%CORE_DIR%\resources\icon.ico" set "ICON_CMD=/win32icon:"%CORE_DIR%\resources\icon.ico""

echo Compiling...
"%CSC_EXE%" /nologo /target:winexe /out:"%PROJ_DIR%\%EXE_NAME%" %ICON_CMD% /r:System.Windows.Forms.dll /r:System.dll "%CORE_DIR%\src\launcher.cs"
if errorlevel 1 (
    echo Compilation failed!
    pause
    exit /b 1
)

echo.
echo ========================================================
echo [SUCCESS] Build completed!
echo Path: %PROJ_DIR%\%EXE_NAME%
echo ========================================================
echo.
exit /b 0
