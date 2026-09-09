@echo off
chcp 65001 >nul
echo ========================================================
echo   Software Cache Cleaner 构建脚本 (Linux/WSL版)
echo ========================================================
echo.

echo 1. 检查 WSL (Windows Subsystem for Linux) 环境...
wsl --status >nul 2>&1
if %errorlevel% neq 0 goto :err_wsl
echo    - WSL 环境可用。

echo.
echo 2. 检查 WSL 主目录中的 Python 虚拟环境 (venv_cleaner_linux)...
wsl test -d ~/venv_cleaner_linux >nul 2>&1
if %errorlevel% neq 0 goto :setup_env
echo    - 已找到现有的 venv_cleaner_linux 虚拟环境。
goto :run_build

:setup_env
echo    - 未找到 venv_cleaner_linux，正在 WSL 中创建 Python 虚拟环境...
wsl python3 -m venv ~/venv_cleaner_linux
if %errorlevel% neq 0 goto :err_venv

echo    - 虚拟环境创建成功，正在安装依赖...
wsl ~/venv_cleaner_linux/bin/pip install -r requirements.txt
if %errorlevel% neq 0 goto :err_pip
echo    - 依赖安装成功。
goto :run_build

:run_build
echo.
echo 3. 调用 WSL 运行 build.sh 脚本进行 Linux 打包...
wsl sed -i "s/\r$//" build.sh
wsl bash ./build.sh
if %errorlevel% neq 0 goto :err_build
goto :success

:success
echo.
echo ========================================================
echo   构建成功！
echo   文件位置: dist/SoftwareCacheCleaner
echo   
echo   如需测试该程序，可在 WSL 中运行以下命令:
echo   1. 复制二进制文件到 Linux 用户主目录:
echo      cp dist/SoftwareCacheCleaner ~/
echo   2. 赋予运行权限并启动:
echo      chmod +x ~/SoftwareCacheCleaner ^&^& ~/SoftwareCacheCleaner
echo ========================================================
echo.
pause
exit /b 0

:err_wsl
echo [错误] 未检测到 WSL 环境！请确保已安装并配置好 WSL (Windows Subsystem for Linux)。
pause
exit /b 1

:err_venv
echo [错误] 在 WSL 中创建虚拟环境失败！请检查是否已安装 python3-venv。
echo (可在 Ubuntu 中运行 'sudo apt install python3-venv' 安装)
pause
exit /b 1

:err_pip
echo [错误] 依赖包安装失败！请检查网络连接或 pip 源配置。
pause
exit /b 1

:err_build
echo [错误] Linux 打包失败！请检查 PyInstaller 构建日志。
pause
exit /b 1
