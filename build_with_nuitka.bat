@echo off
chcp 65001 >nul
echo ==========================================
echo    乙羽的工具箱 - Nuitka 编译脚本
echo ==========================================
echo.
echo [1/3] 正在检查/安装 Nuitka...
python -m pip install -U nuitka zstandard

echo.
echo [2/3] 正在使用 Nuitka 编译... (这通常比 PyInstaller 慢，但兼容性更好)
echo 如果第一次运行，请根据提示按回车安装必要的编译器依赖 (MinGW/CCache)。
echo.

python -m nuitka --standalone --onefile ^
    --enable-plugin=pyqt5 ^
    --windows-console-mode=disable ^
    --output-dir=dist_nuitka ^
    --output-filename="乙羽的工具箱_Nuitka" ^
    --include-data-dir=resources=resources ^
    --include-data-dir=model=model ^
    --include-data-files=msvcp140.dll=./msvcp140.dll ^
    --include-data-files=vcruntime140.dll=./vcruntime140.dll ^
    --include-data-files=vcruntime140_1.dll=./vcruntime140_1.dll ^
    src/demo.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 编译失败！
    pause
    exit /b
)

echo.
echo [3/3] 成功！EXE 已生成在 dist_nuitka 目录下。
echo.
pause
