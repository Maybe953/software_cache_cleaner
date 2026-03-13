import os
import shutil
from pathlib import Path
import sys

# Ensure we can import src modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from cleaner import CacheCleaner

def test_whitelist():
    base_dir = Path(r"D:\360驱动大师目录")
    
    # 1. Setup Environment
    if not base_dir.exists():
        base_dir.mkdir(parents=True)
    
    dirs_to_create = ["a", "b", "c", "should_delete"]
    files_created = []

    print(f"[-] 正在初始化测试环境: {base_dir}")
    for d in dirs_to_create:
        dir_path = base_dir / d
        if not dir_path.exists():
            dir_path.mkdir()
        
        file_path = dir_path / "test_file.txt"
        file_path.write_text("dummy content")
        files_created.append(file_path)
    
    print("[-] 测试文件夹创建完毕: a, b, c, should_delete")

    # 2. Run Cleaner
    print("[-] 实例化清理器...")
    # 将测试目录传入作为自定义路径
    cleaner = CacheCleaner(dry_run=False, custom_paths=[str(base_dir)]) 
    
    print("[-] 开始清理...")
    # 使用标准清理模式
    cleaner.clean()

    # 3. Verify
    print("[-] 验证结果:")
    
    # Check Whitelist
    if (base_dir / "a").exists():
        print("  [PASS] 文件夹 'a' 依然存在")
    else:
        print("  [FAIL] 文件夹 'a' 被删除了!")

    if (base_dir / "b").exists():
        print("  [PASS] 文件夹 'b' 依然存在")
    else:
        print("  [FAIL] 文件夹 'b' 被删除了!")

    # Check Others
    if not (base_dir / "c").exists():
        print("  [PASS] 文件夹 'c' 已被删除")
    else:
        print("  [FAIL] 文件夹 'c' 仍然存在!")
        
    if not (base_dir / "should_delete").exists():
        print("  [PASS] 文件夹 'should_delete' 已被删除")
    else:
        print("  [FAIL] 文件夹 'should_delete' 仍然存在!")

    # Cleanup (Optional)
    # shutil.rmtree(base_dir)

if __name__ == "__main__":
    try:
        test_whitelist()
    except Exception as e:
        print(f"[ERROR] {e}")
