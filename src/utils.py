import os
import math
import sys
import subprocess
import tempfile
import datetime
from xml.sax.saxutils import escape

try:
    import winreg
except ImportError:
    winreg = None

try:
    import ctypes
except ImportError:
    ctypes = None

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
    获取标准的系统临时目录。
    """
    if sys.platform == 'win32':
        return os.environ.get('TEMP', os.path.expanduser('~\\AppData\\Local\\Temp'))
    else:
        return tempfile.gettempdir()

def get_global_config_path() -> str:
    """获取全局配置目录路径，如果不存在则创建"""
    if sys.platform == 'win32':
        program_data = os.environ.get('PROGRAMDATA', 'C:\\ProgramData')
        app_dir = os.path.join(program_data, 'SoftwareCacheCleaner')
    else:
        # Linux 下普通用户无 /etc 写权限，写入用户 ~/.config
        app_dir = os.path.expanduser('~/.config/software_cache_cleaner')
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def is_admin():
    """检查是否拥有管理员权限"""
    if sys.platform == 'win32':
        if ctypes and hasattr(ctypes, 'windll'):
            try:
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                return False
        return False
    else:
        try:
            return os.getuid() == 0
        except Exception:
            return False

def set_autostart(enabled: bool):
    """
    设置自启动。
    Windows: 使用任务计划程序 (Task Scheduler) 和 XML 模板。
    Linux: 写入 ~/.config/autostart 桌面自启动项。
    """
    if sys.platform != 'win32':
        autostart_dir = os.path.expanduser('~/.config/autostart')
        desktop_file = os.path.join(autostart_dir, 'software_cache_cleaner.desktop')
        if enabled:
            try:
                os.makedirs(autostart_dir, exist_ok=True)
                if getattr(sys, 'frozen', False):
                    app_path = sys.executable
                    exec_cmd = f'"{app_path}" --auto-clean'
                else:
                    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
                    app_path = sys.executable
                    exec_cmd = f'"{app_path}" "{script_path}" --auto-clean'
                
                desktop_content = f'''[Desktop Entry]
Type=Application
Exec={exec_cmd}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=SoftwareCacheCleaner
Comment=Software Cache Cleaner Auto Clean
'''
                with open(desktop_file, 'w', encoding='utf-8') as f:
                    f.write(desktop_content)
                os.chmod(desktop_file, 0o755)
                return True
            except Exception as e:
                print(f"DEBUG: 设置 Linux 自启动失败: {e}", flush=True)
                return False
        else:
            try:
                if os.path.exists(desktop_file):
                    os.remove(desktop_file)
                return True
            except Exception as e:
                print(f"DEBUG: 删除 Linux 自启动失败: {e}", flush=True)
                return False

    # Windows 平台实现
    task_name = "SoftwareCacheCleaner"
    
    if getattr(sys, 'frozen', False):
        app_path = f'{sys.executable}'
    else:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
        app_path = sys.executable
        app_args = f'"{script_path}" --auto-clean'
    
    if getattr(sys, 'frozen', False):
        app_args = "--auto-clean"
        
    safe_app_path = escape(app_path)
    safe_app_args = escape(app_args)
        
    try:
        global_log_file = os.path.join(get_global_config_path(), "cleaner_errors.log")
        if enabled:
            try:
                if winreg:
                    run_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                    winreg.DeleteValue(run_key, task_name)
                    winreg.CloseKey(run_key)
            except Exception:
                pass
            subprocess.run(f'schtasks /delete /tn "{task_name}" /f', capture_output=True, shell=True)

            xml_content = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2024-01-01T00:00:00</Date>
    <Author>SoftwareCacheCleaner</Author>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT0S</Delay>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <GroupId>S-1-5-32-545</GroupId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>1</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"{safe_app_path}"</Command>
      <Arguments>{safe_app_args}</Arguments>
    </Exec>
  </Actions>
</Task>'''

            fd, tmp_xml_path = tempfile.mkstemp(suffix=".xml")
            with os.fdopen(fd, 'w', encoding='utf-16') as f:
                f.write(xml_content)
                
            command = f'schtasks /create /tn "{task_name}" /xml "{tmp_xml_path}" /f'
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            
            try:
                if os.path.exists(tmp_xml_path):
                    os.remove(tmp_xml_path)
            except OSError:
                pass
                
            if result.returncode != 0:
                with open(global_log_file, "a", encoding="utf-8") as lf:
                    lf.write(f"\n--- [Autostart Error {datetime.datetime.now()}] ---\n")
                    lf.write(f"Command: {command}\n")
                    lf.write(f"Stderr: {result.stderr}\n")
                return False
            return True
        else:
            command = f'schtasks /delete /tn "{task_name}" /f'
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            if result.returncode == 0 or not check_autostart():
                return True
            else:
                with open(global_log_file, "a", encoding="utf-8") as lf:
                    lf.write(f"\n--- [Autostart Delete Error {datetime.datetime.now()}] ---\n")
                    lf.write(f"Command: {command}\n")
                    lf.write(f"Stderr: {result.stderr}\n")
                return False
    except Exception as e:
        print(f"DEBUG: 设置计划任务自启动出错: {e}", flush=True)
        return False

def check_autostart() -> bool:
    """检查自启动任务是否存在"""
    if sys.platform != 'win32':
        autostart_dir = os.path.expanduser('~/.config/autostart')
        desktop_file = os.path.join(autostart_dir, 'software_cache_cleaner.desktop')
        return os.path.exists(desktop_file)

    task_name = "SoftwareCacheCleaner"
    try:
        command = f'schtasks /query /tn "{task_name}"'
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return result.returncode == 0
    except Exception:
        return False
