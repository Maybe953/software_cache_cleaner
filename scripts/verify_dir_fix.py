import os
import shutil
from pathlib import Path
import sys

# Ensure we can import src modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from cleaner import CacheCleaner

def test_dir_deletion():
    # 使用自定义路径进行测试，避免干扰真实文档
    test_base = Path("D:/test_cleanup_dirs")
    if not test_base.exists():
        test_base.mkdir(parents=True)
    
    # 1. Setup Environment
    dirs_to_create = ["a", "b", "c", "sub/d"]
    for d in dirs_to_create:
        p = test_base / d
        p.mkdir(parents=True, exist_ok=True)
        (p / "file.txt").write_text("content")

    print(f"[-] 测试环境就绪: {list(test_base.glob('*'))}")

    # 2. Run Cleaner
    # Use custom_paths to point to our test dir
    cleaner = CacheCleaner(dry_run=False, custom_paths=[str(test_base)])
    
    print("[-] 执行清理...")
    cleaner.clean()

    # 3. Verify
    print("[-] 验证结果:")
    items = [x.name for x in test_base.iterdir()]
    print(f"  剩余项目: {items}")
    
    if "a" in items and "b" in items:
        print("  [PASS] 文件夹 'a' 和 'b' 被保留了")
    else:
        print("  [FAIL] 文件夹 'a' 或 'b' 丢失了!")

    if "c" not in items:
        print("  [PASS] 文件夹 'c' 已被正确删除")
    else:
        print("  [FAIL] 文件夹 'c' 仍然存在!")

    # Cleanup test dir
    shutil.rmtree(test_base)

if __name__ == "__main__":
    try:
        test_dir_deletion()
    except Exception as e:
        print(f"[ERROR] {e}")
