import os
import math
import sys
import winreg
import subprocess
import ctypes
import tempfile
import datetime
from xml.sax.saxutils import escape

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

def get_global_config_path() -> str:
    """获取所有用户共享的全局配置目录路径，如果不存在则创建"""
    program_data = os.environ.get('PROGRAMDATA', 'C:\\ProgramData')
    app_dir = os.path.join(program_data, 'SoftwareCacheCleaner')
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def is_admin():
    """检查是否拥有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def set_autostart(enabled: bool):
    """
    使用 Windows 任务计划程序 (Task Scheduler) 和 XML 模板设置自启动。
    这种方式支持让任意用户(Builtin\\Users)在登录时，以管理员权限静默执行清理工具。
    """
    task_name = "SoftwareCacheCleaner"
    
    if getattr(sys, 'frozen', False):
        app_path = f'{sys.executable}'
    else:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
        # 若为脚本环境，我们用 python 解释器调用
        app_path = sys.executable
        # 注意：此处不支持含空格的路径，仅作向后兼容
        app_args = f'"{script_path}" --auto-clean'
    
    if getattr(sys, 'frozen', False):
        app_args = "--auto-clean"
        
    # XML 字符转义，防止路径中的极其特殊字符（如 &）破坏 XML 结构
    safe_app_path = escape(app_path)
    safe_app_args = escape(app_args)
        
    try:
        global_log_file = os.path.join(get_global_config_path(), "cleaner_errors.log")
        if enabled:
            # 1. 删除可能存在的旧注册表启动项及旧的计划任务
            try:
                run_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(run_key, task_name)
                winreg.CloseKey(run_key)
            except Exception:
                pass
            subprocess.run(f'schtasks /delete /tn "{task_name}" /f', capture_output=True, shell=True)

            # 2. 生成基于 XML 的高级计划任务模板 
            # (拦截 UAC + 交互式权限全域开启)
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
      <!-- 此处不在 LogonTrigger 中指定 UserId，意味着针对 Any User -->
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

            # 将 XML 写入临时文件供 schtasks 导入
            fd, tmp_xml_path = tempfile.mkstemp(suffix=".xml")
            with os.fdopen(fd, 'w', encoding='utf-16') as f:
                f.write(xml_content)
                
            command = f'schtasks /create /tn "{task_name}" /xml "{tmp_xml_path}" /f'
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            
            # 删除用于注册的临时 XML
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
            # 移除计划任务
            command = f'schtasks /delete /tn "{task_name}" /f'
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            
            # 检查结果：如果删除成功，或者任务已经不存在（也算成功）
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
    task_name = "SoftwareCacheCleaner"
    try:
        command = f'schtasks /query /tn "{task_name}"'
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return result.returncode == 0
    except Exception:
        return False
