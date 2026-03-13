import os
import shutil
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from cleaner import CacheCleaner

def test_whitelist():
    test_root = Path("test_env")
    if test_root.exists():
        shutil.rmtree(test_root)
    test_root.mkdir()

    # Create mock WXWorkLocal structure
    wx_root = test_root / "Documents" / "WXWorkLocal"
    wx_root.mkdir(parents=True)

    # 1. Whitelisted user 'a' (lowercase on disk, lowercase in whitelist)
    user_a = wx_root / "a"
    user_a.mkdir()
    (user_a / "Cache").mkdir()
    (user_a / "Cache" / "file_a.txt").write_text("should be protected")

    # 2. Whitelisted user 'B' (uppercase on disk, lowercase in whitelist)
    user_b = wx_root / "B"
    user_b.mkdir()
    (user_b / "Cache").mkdir()
    (user_b / "Cache" / "file_b.txt").write_text("should be protected (case insensitive)")

    # 3. Non-whitelisted user 'c'
    user_c = wx_root / "c"
    user_c.mkdir()
    (user_c / "Cache").mkdir()
    (user_c / "Cache" / "file_c.txt").write_text("should be deleted")

    # 4. Whitelisted user ' d' (with leading space)
    user_d = wx_root / " d"
    user_d.mkdir()
    (user_d / "Cache").mkdir()
    (user_d / "Cache" / "file_d.txt").write_text("protected (strip check)")

    # 5. Root file (should be protected by default)
    (wx_root / "important_config.ini").write_text("protected root file")

    print(f"--- 模拟环境创建完成 ---")
    print(f"名单: a, b, d")

    # Initialize cleaner with whitelist
    cleaner = CacheCleaner(dry_run=False, whitelist=['a', ' b', 'd'])
    cleaner.targets = [wx_root]

    # Test Scan
    print("\n[开始扫描测试]")
    results = cleaner.scan(progress_callback=print)
    
    # Test Clean
    print("\n[开始清理测试]")
    removed, freed, errors = cleaner.clean(progress_callback=print)

    print(f"\n清理总结: 删除 {removed} 个文件, 释放 {freed} 字节")
    if errors:
        print(f"错误: {errors}")

    # Verification
    print("\n[结果校验]")
    
    a_cache_exists = (user_a / "Cache").exists()
    b_cache_exists = (user_b / "Cache").exists()
    c_cache_exists = (user_c / "Cache").exists()
    d_cache_exists = (user_d / "Cache").exists()
    root_file_exists = (wx_root / "important_config.ini").exists()

    success = True
    if a_cache_exists:
        print("✅ 账号 'a' 的 Cache 已成功跳过 (白名单命中)")
    else:
        print("❌ 账号 'a' 的 Cache 被错误删除了!")
        success = False

    if b_cache_exists:
        print("✅ 账号 'B' 的 Cache 已成功跳过 (大小写不敏感)")
    else:
        print("❌ 账号 'B' 的 Cache 被错误删除了!")
        success = False

    if d_cache_exists:
        print("✅ 账号 ' d ' (带空格) 已成功跳过 (strip 匹配成功)")
    else:
        print("❌ 账号 ' d ' 被错误删除了!")
        success = False

    if not c_cache_exists:
        print("✅ 账号 'c' 的 Cache 已正确清理 (不在白名单)")
    else:
        print("❌ 账号 'c' 的 Cache 仍然存在!")
        success = False

    if root_file_exists:
        print("✅ WXWorkLocal 根目录文件已正确保护")
    else:
        print("❌ WXWorkLocal 根目录文件被删除了!")
        success = False

    # Cleanup test env
    if test_root.exists():
        shutil.rmtree(test_root)

    if success:
        print("\n🏆 白名单逻辑所有测试点均已通过!")
    else:
        print("\n🚨 白名单逻辑存在漏洞，需要修复。")

if __name__ == "__main__":
    test_whitelist()
