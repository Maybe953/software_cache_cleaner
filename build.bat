@echo off
chcp 65001
echo ========================================================
echo   Software Cache Cleaner 构建脚本 (内网版)
echo ========================================================
echo.
echo [注意] 本脚本假设当前环境已安装所有必要依赖 (pyinstaller, rich, customtkinter, pywin32 等)
echo [注意] 内网环境不执行 pip install 操作
echo.

echo 0. 尝试关闭可能正在运行的旧进程...
taskkill /f /im "SoftwareCacheCleaner.exe" >nul 2>&1
timeout /t 1 /nobreak >nul

echo 1. 清理旧的构建文件...
if exist dist\SoftwareCacheCleaner.exe (
    del /f /q dist\SoftwareCacheCleaner.exe || (
        echo [错误] 无法删除旧的 EXE 文件，请确认它已关闭！
        pause
        exit /b 1
    )
)
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo.
echo 2. 开始使用 PyInstaller 打包...
echo    - 入口文件: src/main.py
echo    - 模式: 单文件 EXE, 无控制台
echo    - 权限: 强制管理员启动 (--uac-admin)
echo.

echo    - 依赖: 自动收集 customtkinter
echo    - 图标: assets/icon.ico
echo.

.\venv\Scripts\pyinstaller --noconsole --onefile --clean --uac-admin --name "SoftwareCacheCleaner" --icon="assets/icon.ico" --collect-all customtkinter src/main.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 打包失败！请检查 PyInstaller 是否安装。
    pause
    exit /b %errorlevel%
)

echo.
echo 3. 复制配置文件...
if exist config.json (
    copy config.json dist\
    echo    - 已复制 config.json
) else (
    echo    - [警告] config.json 未找到，将跳过复制
)

echo.
echo ========================================================
echo   构建成功！
echo   文件位置: dist\SoftwareCacheCleaner.exe
echo ========================================================
echo.
pause
