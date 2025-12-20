@echo off
chcp 65001 >nul
echo ==========================================
echo       乙羽的工具箱 - 强力镜像同步脚本
echo ==========================================
echo.
echo 注意：此脚本会将把本地的所有变动（包括删除）同步到 GitHub。
echo 如果您在本地删除了文件，运行此脚本后，GitHub 上也会被删除。
echo.

:: 1. 强制添加所有变动 (包含删除操作)
echo [1/3]正在扫描变动 (git add -A)...
git add -A

:: 2. 提交变动
echo [2/3]正在提交更改...
set "timestamp=%date:~0,10% %time:~0,8%"
git commit -m "Mirror sync: %timestamp%"

:: 3. 推送
echo [3/3]正在同步到 GitHub...
git push origin main

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 同步失败！
    color 0c
) else (
    echo.
    echo [SUCCESS] 镜像同步完成！远程仓库已与本地保持一致。
    color 0a
)

echo.
pause
