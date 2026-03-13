import sys
import os
import winreg

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from utils import set_autostart

def verify_cleanup_logic():
    print("[-] 正在验证关闭清理逻辑...")
    
    # 1. 模拟写入一个假的 HKCU 键值（作为残留项）
    hkcu_run = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hkcu_run, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "SoftwareCacheCleaner", 0, winreg.REG_SZ, "DummyPath")
        winreg.CloseKey(key)
        print("  [SETUP] 已在 HKCU 中创建了测试用的残留启动项")
    except Exception as e:
        print(f"  [ERROR] Setup failed: {e}")
        return

    # 2. 调用 set_autostart(False)
    # 预期：HKLM 会因为没权限而报错（但在代码内部会被捕获或打印），但关键是它应该能把我们的 HKCU 删掉
    print("[-] 执行 set_autostart(False)...")
    result = set_autostart(False)
    
    # 3. 验证 HKCU 是否已消失
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hkcu_run, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, "SoftwareCacheCleaner")
            print("  [FAIL] HKCU 中的残留项仍然存在！代码没有执行清理逻辑。")
        except FileNotFoundError:
            print("  [PASS] HKCU 中的残留项已被成功清理！")
        winreg.CloseKey(key)
    except Exception as e:
        print(f"  [ERROR] Verification failed: {e}")

if __name__ == "__main__":
    verify_cleanup_logic()
