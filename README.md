# Software Cache Cleaner (软件缓存清理工具) - V4.0 全域清理版

## 项目简介
Software Cache Cleaner 是一款专为 Windows 环境设计的轻量级、高效缓存清理工具。它不仅能清理当前用户的系统临时文件，还能自动识别并清理系统中**所有用户**的临时目录、图片文件夹以及企业微信 (WeChat Work) 的缓存数据。

该工具支持**严格的白名单保护机制**，确保重要账号的数据在清理过程中绝对安全。

---

## 核心功能

1.  **全域扫描 (Cross-User Scanning)**：
    *   自动识别 `C:\Users\*` 下所有活跃用户的目录。
    *   清理各用户 `AppData\Local\Temp` 临时目录。
    *   清理各用户 `Pictures` 图片保存目录。
    *   清理各用户 `Documents\WXWorkLocal` 企业微信缓存目录。
2.  **企业微信专项防护**：
    *   **深度指纹识别**：仅清理路径中包含 `Cache` 关键字的文件/目录。
    *   **结构保护**：完美保留账号根目录及 `File`、`Video` 等非缓存业务文件夹。
3.  **严格白名单机制**：
    *   支持**大小写敏感**的账号过滤。
    *   一旦匹配白名单，该目录及其所有子项在扫描和清理阶段均会被彻底忽略（物理隔离）。
4.  **双模式运行**：
    *   **GUI 模式**：基于 `CustomTkinter` 的现代图形界面，支持实时日志、进度条和安全模式开关。
    *   **CLI 模式**：支持命令行参数，便于集成到自动化运维脚本中。
5.  **静默自启动**：
    *   支持通过 Windows 任务计划程序 (Task Scheduler) 实现开机自动后台清理，无 UAC 弹窗干扰。

---

## 快速开始

### 环境依赖
*   Python 3.9+
*   主要第三方库：`customtkinter`, `rich`, `pywin32`, `pillow`, `send2trash`

### 安装
```bash
pip install -r requirements.txt
```

### 运行
1.  **图形界面 (推荐)**：
    ```bash
    python src/main.py
    ```
    *注意：若需清理其他用户目录，请使用“以管理员身份运行”启动终端或运行程序。*

2.  **命令行模式**：
    *   扫描：`python src/main.py --scan`
    *   强制清理：`python src/main.py --clean --force`

---

## 配置说明 (`config.json`)

项目根目录下的 `config.json` 用于持久化存储您的个性化设置：

```json
{
    "custom_paths": [],
    "whitelist": [
        "ZhangSan",
        "LiSi"
    ]
}
```
*   `custom_paths`: 手动添加的额外清理路径。
*   `whitelist`: **严格区分大小写**的保护名单（对应文件夹名）。

---

## 打包工具

项目内置了 `build.bat` 脚本，用于生成单文件绿色版 EXE：
*   **特性**：自动收集 `customtkinter` 依赖，嵌入程序图标，强制管理员权限运行。
*   **生成位置**：`dist/SoftwareCacheCleaner.exe`

---

## 目录结构
*   `src/`: 核心源代码（清理引擎、GUI、工具类）。
*   `assets/`: 静态资源（图标等）。
*   `scripts/`: 验证脚本和开发辅助工具。
*   `config.json`: 配置文件。
*   `README.md`: 本说明文档。

---

## 安全警示
> [!IMPORTANT]
> 本程序在非白名单下的微信目录执行递归清理时会删除所有包含 `Cache` 关键字的内容。请在正式清理前务必开启 **“安全模式 (仅模拟)”** 进行扫描确认。
