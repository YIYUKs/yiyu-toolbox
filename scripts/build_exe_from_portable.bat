@echo off
chcp 65001 >nul
echo ==========================================
echo    乙羽的工具箱 - 从便携环境构建 EXE
echo ==========================================
echo.
echo 既然【绿色便携版】可以运行，说明那个环境里的库是正确的。
echo 本脚本将利用便携版的运行环境来打包 EXE。
echo.

set PORTABLE_DIR=乙羽的工具箱_绿色便携版
set RUNTIME=%PORTABLE_DIR%\runtime

if not exist "%RUNTIME%" (
    echo [!] 错误：未找到便携版环境！
    echo 请先运行一次【create_portable_version.bat】确保便携文件夹已生成。
    pause
    exit /b
)

echo [1/3] 正在便携环境中安装 PyInstaller...
"%RUNTIME%\Scripts\pip" install pyinstaller

echo [2/3] 正在开始打包 (使用便携版的纯净环境)...
:: 使用 venv 里的 pyinstaller
"%RUNTIME%\Scripts\pyinstaller" --noconfirm --onedir --windowed --clean ^
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
    src/demo.py

if %errorlevel% neq 0 (
    echo [ERROR] 打包过程中出现错误！
    pause
    exit /b
)

echo [3/3] 正在执行 OpenMP 冲突修复 (物理移除重复 DLL)...
:: 这是一个经典的 PyInstaller + Torch 修复：如果根目录和 internal 都有 libiomp5md.dll，尝试统一到一个
set TARGET_DIR=dist\乙羽的工具箱
if exist "%TARGET_DIR%\_internal\torch\lib\libiomp5md.dll" (
    echo [*] 正在检测并修复 OpenMP 命名空间冲突...
    :: 如果 PyTorch 的 DLL 初始化失败，通常是因为它加载了错误的 OpenMP 副本
    copy "%TARGET_DIR%\_internal\torch\lib\libiomp5md.dll" "%TARGET_DIR%\" /y
)

echo.
echo ==========================================
echo  构建完成！请尝试运行 dist\乙羽的工具箱\乙羽的工具箱.exe
echo.
echo  如果这最后一次尝试仍然报 1114 错误，
echo  那就说明 PyInstaller 的引导加载程序与这台电脑上的 Torch 驱动确实不兼容。
echo  此时【绿色便携版】将不再是备选，而是本项目的【唯一推荐正式版】。
echo ==========================================
pause
