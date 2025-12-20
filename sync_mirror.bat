@echo off
setlocal
chcp 65001 >nul
title 乙羽的工具箱 - 同步助手

echo ==========================================
echo       乙羽的工具箱 - 镜像同步脚本
echo ==========================================
echo.
echo [提示] 本脚本会将本地所有变动同步到远程仓库。
echo.

:: 1. 扫描变动
echo [1/3] 正在添加文件 (git add)...
git add -A

:: 2. 提交变动
echo [2/3] 正在提交 (git commit)...
set "timestamp=%date:~0,10% %time:~0,8%"
git commit -m "Mirror sync: %timestamp%"

:: 3. 推送
echo [3/3] 正在推送到 GitHub...
git push origin main

if errorlevel 1 (
    echo.
    echo ==========================================
    echo [错误] 推送失败！
    echo ==========================================
    echo 可能原因:
    echo 1. 网络连接问题 (Could not resolve host) - 请检查代理或网络。
    echo 2. 远程仓库权限问题。
    echo.
    echo 请尝试手动运行: git push origin main
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo [成功] 同步完成！
    pause
    exit /b 0
)
