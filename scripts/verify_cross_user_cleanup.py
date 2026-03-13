import os
import shutil
import sys
from pathlib import Path

# 将 src 加入路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from cleaner import CacheCleaner

def create_mock_environment(base_path: Path):
    if base_path.exists():
        shutil.rmtree(base_path)
    base_path.mkdir(parents=True)

    # 模拟用户环境
    # 用户 1: 有白名单账号 'a' (小写) 和 'B' (大写)
    # 用户 2: 有普通账号 'c'
    # 注意：默认白名单包含 'a' 和 'b'
    
    structure = {
        # 'a' 完全匹配白名单 -> 应保留
        "User1/Documents/WXWorkLocal/a/Cache/file1.txt": "protected",
        "User1/Documents/WXWorkLocal/a/File/doc1.txt": "protected",
        
        # 'B' 大小写不匹配白名单 'b' -> 应删除
        "User1/Documents/WXWorkLocal/B/Cache/file2.txt": "should_delete",
        
        # 'c' 不在白名单 -> Cache 应删除
        "User2/Documents/WXWorkLocal/c/Cache/file3.txt": "should_delete",
        "User2/Documents/WXWorkLocal/c/File/doc2.txt": "should_keep",
        
        # 'd' 不在白名单 -> Cache 应删除
        "User2/Documents/WXWorkLocal/d/Cache/file4.txt": "should_delete",
    }

    for path_str, content in structure.items():
        file_path = base_path / path_str
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        
    # 创建一个空的非 Cache 文件夹 (验证防误删)
    (base_path / "User2/Documents/WXWorkLocal/c/EmptyNotes").mkdir(parents=True, exist_ok=True)
        
    return base_path

def verify_cross_user_cleanup():
    cwd = Path.cwd()
    mock_root = cwd / "MockUsers"
    
    print(f"[-] 创建模拟环境: {mock_root}")
    create_mock_environment(mock_root)
    
    targets = []
    targets.append(str(mock_root / "User1/Documents/WXWorkLocal"))
    targets.append(str(mock_root / "User2/Documents/WXWorkLocal"))
    
    print(f"[-] 初始化清理器...")
    # 实例化 Cleaner，非 dry_run 模式
    # 注意：Cleaner 内部的 protected_names 默认含 'a', 'b' (但现在是严格匹配)
    cleaner = CacheCleaner(dry_run=False, custom_paths=targets)
    
    print(f"[-] 开始清理...")
    files, freed, errors = cleaner.clean()
    
    print(f"[-] 清理完成: 删除了 {files} 个文件, 释放了 {freed} 字节")
    if errors:
        print(f"[-] 错误信息: {errors}")

    print("\n[-] 验证结果:")
    
    # 验证逻辑
    checks = [
        # 白名单 'a' - 应该完全保留
        ("User1/Documents/WXWorkLocal/a/Cache/file1.txt", True, "白名单 'a' (完全匹配) 的 Cache 文件应保留"),
        ("User1/Documents/WXWorkLocal/a/File/doc1.txt", True, "白名单 'a' (完全匹配) 的普通文件应保留"),
        
        # 账号 'B' - 由于现在改成了严格大小写匹配，'B' 不匹配白名单 'b'，所以 'B' 应该被清理
        ("User1/Documents/WXWorkLocal/B/Cache/file2.txt", False, "账号 'B' (大写) 不匹配白名单 'b'，应被清理"),
        
        # 普通账号 'c' - Cache 应该被删，File 应该保留
        ("User2/Documents/WXWorkLocal/c/Cache/file3.txt", False, "普通账号 'c' 的 Cache 文件应删除"),
        ("User2/Documents/WXWorkLocal/c/File/doc2.txt", True, "普通账号 'c' 的普通文件应保留"),
        
        # 普通账号 'c' 的 Cache 文件夹本身应被删
        ("User2/Documents/WXWorkLocal/c/Cache", False, "普通账号 'c' 的 Cache 目录本身应被删除"),
        
        # 普通账号 'd' - Cache 应该被删
        ("User2/Documents/WXWorkLocal/d/Cache/file4.txt", False, "普通账号 'd' 的 Cache 文件应删除"),

        # 核心验证：普通账号 'c' 的非 Cache 空文件夹 - 应该保留
        ("User2/Documents/WXWorkLocal/c/EmptyNotes", True, "普通账号 'c' 的非 Cache 空文件夹应保留"),
    ]
    
    all_pass = True
    for rel_path, should_exist, msg in checks:
        full_path = mock_root / rel_path
        exists = full_path.exists()
        
        if exists == should_exist:
            print(f"  [PASS] {msg}")
        else:
            print(f"  [FAIL] {msg} (Expect Exists: {should_exist}, Actual: {exists})")
            all_pass = False
            
    if all_pass:
        print("\n[SUCCESS] 所有验证通过！")
        sys.exit(0)
    else:
        print("\n[FAILURE] 存在验证失败项！")
        sys.exit(1)

if __name__ == "__main__":
    verify_cross_user_cleanup()
