import sys
import os
import winreg

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from utils import set_autostart, check_autostart

def verify_hklm():
    print("[-] 正在测试系统级自启动设置 (HKLM)...")
    
    # 尝试设置开启
    print("[-] 尝试写入 HKEY_LOCAL_MACHINE...")
    success = set_autostart(True)
    
    if success:
        print("  [SUCCESS] 写入成功！当前终端拥有管理员权限。")
        
        # Double check where it wrote
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, "SoftwareCacheCleaner")
            print(f"  [VERIFIED] 在 HKLM 中读取到值: {val}")
            winreg.CloseKey(key)
        except Exception as e:
            print(f"  [ERROR] 虽然写入返回 True，但无法读取 HKLM: {e}")
            
        # Cleanup
        print("[-] 清理测试键值...")
        set_autostart(False)
        
    else:
        print("  [FAILED] 写入失败。")
        print("  [INFO] 这是预期行为：因为操作 HKEY_LOCAL_MACHINE 需要管理员权限。")
        print("  [INFO] 只要这里失败是由“拒绝访问”引起的，就证明代码确实是在尝试操作全用户配置。")

if __name__ == "__main__":
    verify_hklm()
