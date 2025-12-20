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

:: 使用 python -m PyInstaller 调用，尝试恢复默认的 _internal 结构以获得更好的兼容性
python -m PyInstaller --noconfirm --onedir --windowed --clean ^
    --name "乙羽的工具箱" ^
    --icon "resources/icon.png" ^
    --add-data "resources;resources" ^
    --add-data "model;model" ^
    --add-binary "msvcp140.dll;." ^
    --add-binary "msvcp140_1.dll;." ^
    --add-binary "msvcp140_2.dll;." ^
    --add-binary "vcruntime140.dll;." ^
    --add-binary "vcruntime140_1.dll;." ^
    --collect-all "torch" ^
    --collect-all "scenedetect" ^
    --hidden-import "cv2" ^
    --hidden-import "numpy" ^
    --hidden-import "PyQt5" ^
    --hidden-import "torch.utils.data.datapipes.utils.common" ^
    src/demo.py

if %errorlevel% neq 0 (
    echo [ERROR] 编译失败！
    color 0c
    pause
    exit /b %errorlevel%
)

echo [2/2] 正在执行“手动环境对齐”修复...
:: 复制关键 DLL 到根目录，这是解决 WinError 1114 的通用物理补丁
set DIST_PATH=dist\乙羽的工具箱
set TORCH_PATH=%DIST_PATH%\_internal\torch\lib
if exist "%TORCH_PATH%" (
    echo [*] 正在将 torch 核心组件提取至根目录...
    copy "%TORCH_PATH%\c10.dll" "%DIST_PATH%\" /y
    copy "%TORCH_PATH%\torch_cpu.dll" "%DIST_PATH%\" /y
    copy "%TORCH_PATH%\asmjit.dll" "%DIST_PATH%\" /y
    copy "%TORCH_PATH%\libiomp5md.dll" "%DIST_PATH%\" /y
)

echo.
echo [OK] 构建成功！
echo ==========================================
echo  程序已生成在: %DIST_PATH%\
echo  如果运行仍有 1114 错误，说明本项目在该环境下的最佳方案
echo  就是你刚才测试成功的“绿色便携版”。
echo ==========================================
pause
color 0a
pause
