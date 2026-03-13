import os
import math
import sys
import winreg
import subprocess
import ctypes

def format_size(size_bytes: int) -> str:
    """
    将字节大小格式化为易读的字符串（KB、MB、GB等）。
    """
    if size_bytes == 0:
        return "0 B"
    
    size_name = ("B", "KB", "MB", "GB", "TB")
    if size_bytes > 0:
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"
    return "0 B"

def get_system_temp_dir() -> str:
    """
    获取标准的 Windows 临时目录。
    """
    return os.environ.get('TEMP', os.path.expanduser('~\\AppData\\Local\\Temp'))

def is_admin():
    """检查是否拥有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def set_autostart(enabled: bool):
    """
    使用 Windows 任务计划程序 (Task Scheduler) 设置或移除自启动任务。
    这种方式可以绕过 UAC 拦截，以最高权限静默启动。
    """
    task_name = "SoftwareCacheCleaner"
    
    # 获取可执行文件或脚本路径
    if getattr(sys, 'frozen', False):
        # 打包后的应用，包含引导参数
        app_path = f'"{sys.executable}" --auto-clean'
    else:
        # 开发模式下的脚本路径
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
        app_path = f'"{sys.executable}" "{script_path}" --auto-clean'

    try:
        if enabled:
            # 1. 尝试删除旧的注册表自启动项 (如果存在)
            try:
                run_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(run_key, task_name)
                winreg.CloseKey(run_key)
            except Exception:
                pass

            # 2. 调用 schtasks 创建任务
            # 必须对整个执行命令行加引号，且内部路径引号需转义
            escaped_app_path = app_path.replace('"', '\\"')
            command = f'schtasks /create /tn "{task_name}" /tr "{escaped_app_path}" /sc onlogon /rl highest /f'
            
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            if result.returncode != 0:
                import logging
                logging.error(f"schtasks 创建失败: {result.stderr}")
                return False
            return True
        else:
            # 移除计划任务
            command = f'schtasks /delete /tn "{task_name}" /f'
            subprocess.run(command, capture_output=True, text=True, shell=True)
            return True
    except Exception as e:
        import logging
        logging.error(f"设置计划任务自启动出错: {e}")
        return False

def check_autostart() -> bool:
    """检查自启动任务是否存在"""
    task_name = "SoftwareCacheCleaner"
    try:
        command = f'schtasks /query /tn "{task_name}"'
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return result.returncode == 0
    except Exception:
        return False
