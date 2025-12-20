@echo off
chcp 65001 >nul
echo ==========================================
echo       乙羽的工具箱 - EXE 构建脚本
echo ==========================================
echo.

:: 清理旧的构建文件
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "*.spec" del /q "*.spec"

echo [1/2] 正在分析依赖并构建 EXE...
echo 这可能需要几分钟，请耐心等待 (依赖包很大)...

:: 使用 python -m PyInstaller 调用，避免环境变量问题
:: 移除了命令块内的中文注释，防止转义错误
python -m PyInstaller --noconfirm --onedir --windowed --clean ^
    --name "乙羽的工具箱" ^
    --icon "resources/icon.png" ^
    --add-data "resources;resources" ^
    --add-data "model;model" ^
    --hidden-import "torch" ^
    --hidden-import "cv2" ^
    --hidden-import "numpy" ^
    --hidden-import "PyQt5" ^
    src/demo.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 构建失败！请检查报错信息。
    color 0c
    pause
    exit /b
)

echo.
echo [2/2] 构建成功！
echo.
echo ==========================================
echo  程序已生成在: dist\乙羽的工具箱\
echo  请将整个文件夹压缩后发给他人使用。
echo ==========================================
echo.
color 0a
pause
