#!/bin/bash
# ========================================================
#   Software Cache Cleaner 构建脚本 (Linux版)
# ========================================================

# 解决脚本路径问题，确保在项目根目录下执行
cd "$(dirname "$0")"

echo "========================================================"
echo "  Software Cache Cleaner 构建脚本 (Linux版)"
echo "========================================================"
echo ""

# 1. 清理旧的构建文件
echo "1. 清理旧的构建文件..."
rm -rf build dist

# 2. 开始使用 PyInstaller 打包
echo "2. 开始使用 PyInstaller 打包..."
# 注意：Linux 下不能使用 Windows 特有的 --uac-admin 和 .ico 图标
# 我们使用 python 环境下的 pyinstaller 执行打包
if [ -d "$HOME/venv_cleaner_linux" ]; then
    PYTHON_BIN="$HOME/venv_cleaner_linux/bin/pyinstaller"
elif [ -d ".venv_linux" ]; then
    PYTHON_BIN=".venv_linux/bin/pyinstaller"
elif [ -d ".venv" ]; then
    PYTHON_BIN=".venv/bin/pyinstaller"
else
    PYTHON_BIN="pyinstaller"
fi

# 1.5. 创建 Linux 本地临时打包目录，规避 NTFS 挂载分区 chmod 权限限制问题
TMP_BUILD="/tmp/cleaner_build"
TMP_DIST="/tmp/cleaner_dist"
rm -rf "$TMP_BUILD" "$TMP_DIST"
mkdir -p "$TMP_BUILD" "$TMP_DIST"

$PYTHON_BIN --noconsole --onefile --clean --name "SoftwareCacheCleaner" \
    --workpath "$TMP_BUILD" \
    --distpath "$TMP_DIST" \
    --collect-all customtkinter src/main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[错误] 打包失败！请确保已安装 PyInstaller。"
    rm -rf "$TMP_BUILD" "$TMP_DIST"
    exit 1
fi

echo ""
echo "3. 将打包好的程序复制回项目的 dist 目录..."
mkdir -p dist
cp "$TMP_DIST/SoftwareCacheCleaner" dist/

echo ""
echo "4. 复制配置文件..."
if [ -f config.json ]; then
    cp config.json dist/
    echo "   - 已复制 config.json"
else
    echo "   - [警告] config.json 未找到，跳过复制"
fi

# 清理临时构建目录
rm -rf "$TMP_BUILD" "$TMP_DIST"

echo ""
echo "========================================================"
echo "  构建成功！"
echo "  文件位置: dist/SoftwareCacheCleaner"
echo "========================================================"
echo ""
