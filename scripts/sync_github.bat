@echo off
chcp 65001 >nul
echo ==========================================
echo       乙羽的工具箱 - GitHub 自动同步脚本
echo ==========================================
echo.

:: 1. 添加所有变动
echo [1/3]正在添加文件 (git add)...
cd /d "%~dp0.."
git add .

:: 2. 提交变动 (自动生成时间戳)
echo [2/3]正在提交更改 (git commit)...
set "timestamp=%date:~0,10% %time:~0,8%"
git commit -m "Auto update: %timestamp%"

:: 3. 推送到远程仓库
echo [3/3]正在推送到 GitHub (git push)...
git push origin main

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 同步失败！请检查网络或配置。
    color 0c
) else (
    echo.
    echo [SUCCESS] 同步成功！所有更改已上传至 GitHub。
    color 0a
)

echo.
pause
