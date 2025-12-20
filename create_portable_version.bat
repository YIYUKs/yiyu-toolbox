@echo off
:: 使用 ANSI 兼容模式，避免 UTF-8 BOM 问题
chcp 65001 >nul
title 乙羽的工具箱 - 构建调试版

echo ========================================================
echo   构建脚本调试模式
echo ========================================================
echo.

set "PROJ_DIR=yiyu_toolbox_portable"
set "EXE_NAME=乙羽的工具箱.exe"

:: 1. 检查和创建目录
echo [Step 1] 检查输出目录...
if exist "%PROJ_DIR%" (
    echo    目录已存在: %PROJ_DIR%
) else (
    echo    创建目录: %PROJ_DIR%
    mkdir "%PROJ_DIR%"
)
if errorlevel 1 goto error_handler

:: 2. 检查环境
echo [Step 2] 检查 Python Runtime...
if exist "%PROJ_DIR%\runtime\Scripts\python.exe" (
    echo    Runtime check: OK
) else (
    echo    Runtime check: 不存在，开始创建...
    python -m venv "%PROJ_DIR%\runtime"
)
if errorlevel 1 goto error_handler

:: 3. 安装依赖
echo [Step 3] 安装/检查依赖...
"%PROJ_DIR%\runtime\Scripts\pip" install -r requirements.txt
if errorlevel 1 (
    echo [警报] pip 安装返回了错误，可能是网络问题，但我们将尝试继续...
)

:: 4. 复制资源
echo [Step 4] 复制核心文件...
xcopy /s /e /y "src" "%PROJ_DIR%\src\" >nul
xcopy /s /e /y "resources" "%PROJ_DIR%\resources\" >nul
xcopy /s /e /y "model" "%PROJ_DIR%\model\" >nul
:: DLL 复制
if not exist "%PROJ_DIR%\runtime\Scripts" mkdir "%PROJ_DIR%\runtime\Scripts"
copy *.dll "%PROJ_DIR%\runtime\Scripts\" /y >nul

:: 5. 编译 EXE
echo [Step 5] 开始编译 EXE...
set "CSC_EXE=C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

if not exist "%CSC_EXE%" (
    echo [错误] 找不到64位编译器: %CSC_EXE%
    echo 尝试寻找32位版本...
    set "CSC_EXE=C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
)

if not exist "%CSC_EXE%" (
    echo [致命错误] 系统中找不到微软 .NET csc.exe 编译器！
    goto error_handler
)

echo    编译器路径: %CSC_EXE%

:: 检查图标
set "ICON_CMD="
if exist "resources\icon.ico" (
    echo    发现图标文件，将启用图标支持。
    set "ICON_CMD=/win32icon:resources\icon.ico"
) else (
    echo    [提示] 未找到 resources\icon.ico，生成无图标版。
)

:: 执行编译命令 (这是最容易出错的一步)
echo.
echo    正在执行编译指令...
"%CSC_EXE%" /nologo /target:winexe /out:"%PROJ_DIR%\%EXE_NAME%" %ICON_CMD% /r:System.Windows.Forms.dll /r:System.dll src\launcher.cs
if errorlevel 1 (
    echo.
    echo [编译失败] csc.exe 返回了错误代码。
    goto error_handler
)

if not exist "%PROJ_DIR%\%EXE_NAME%" (
    echo.
    echo [编译失败] 命令执行完了，但没有生成文件。
    goto error_handler
)

echo.
echo ========================================================
echo [成功] 构建完成！
echo 文件位于: %PROJ_DIR%\%EXE_NAME%
echo ========================================================
echo.
pause
exit /b 0

:error_handler
echo.
echo ========================================================
echo [失败] 构建过程中遇到错误，请截图发给开发者。
echo ========================================================
echo.
pause
exit /b 1
