import os
import shutil
import sys
import time
from pathlib import Path

# 将 src 加入路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from cleaner import CacheCleaner

def setup_test_env(root: Path):
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    # 模拟各类路径
    structure = {
        # 1. Pictures - 用户照片 (风险点)
        "Pictures/vacation_photo.jpg": "USER_PHOTO_SHOULD_KEEP",
        "Pictures/screenshot.png": "USER_SCREENSHOT_SHOULD_KEEP",
        
        # 2. WXWorkLocal - 企业微信 (逻辑点)
        "Documents/WXWorkLocal/User1/Cache/temp_1.jpg": "CACHE_FILE_SHOULD_DELETE",
        "Documents/WXWorkLocal/User1/File/meeting_notes.pdf": "BUSINESS_DOC_SHOULD_KEEP",
        
        # 3. Downloads - 浏览器下载 (后缀点)
        "Downloads/report.pdf": "DOWNLOADED_PDF_SHOULD_DELETE",
        "Downloads/installer.exe": "EXECUTABLE_SHOULD_KEEP",
        
        # 4. Temp - 标准临时文件 (正常点)
        "AppData/Local/Temp/temp_cache.tmp": "TEMP_FILE_SHOULD_DELETE",
    }

    for rel_path, content in structure.items():
        p = root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        
    # 创建一个只读文件测试权限静默失败
    readonly_file = root / "Downloads/readonly.jpg"
    readonly_file.write_text("READONLY_TEST")
    os.chmod(readonly_file, 0o444) # 只读
    
    return root

def run_test():
    test_root = Path.cwd() / "MockSystem"
    print(f"[*] 准备模拟环境: {test_root}")
    setup_test_env(test_root)
    
    targets = [
        test_root / "Pictures",
        test_root / "Documents/WXWorkLocal",
        test_root / "Downloads",
        test_root / "AppData/Local/Temp"
    ]
    
    print("\n[Case 1] 正式清理模式测试")
    cleaner = CacheCleaner(dry_run=False, custom_paths=[str(t) for t in targets])
    # 强制让 cleaner 只处理我们模拟的这几个 target，避免扫到真实系统
    cleaner.targets = targets 
    
    removed, freed, errors = cleaner.clean()
    print(f"结果: 删除了 {removed} 个文件, 错误: {len(errors)}")
    
    # 验证结果
    print("\n详细验证:")
    results = [
        ("Pictures/vacation_photo.jpg", True, "[风险] 用户照片本应保留，实际："),
        ("Documents/WXWorkLocal/User1/Cache/temp_1.jpg", False, "[逻辑] WX 缓存应删除，实际："),
        ("Documents/WXWorkLocal/User1/File/meeting_notes.pdf", True, "[风险] WX 业务文档应保留，实际："),
        ("Downloads/report.pdf", False, "[预期] 下载的 PDF 应删除，实际："),
        ("Downloads/installer.exe", True, "[预期] 下载的 EXE 应保留 (无后缀)，实际："),
        ("Downloads/readonly.jpg", True, "[权限] 只读文件因静默失败会被保留，实际："),
        ("AppData/Local/Temp/temp_cache.tmp", False, "[预期] Temp 缓存应删除，实际："),
    ]
    
    for rel_path, should_exist, msg in results:
        p = test_root / rel_path
        exists = p.exists()
        status = "PASSED" if exists == should_exist else "FAILED"
        print(f"  {msg} {'存在' if exists else '已删除'} -> {status}")

    # Cleanup readonly file before rmtree
    os.chmod(test_root / "Downloads/readonly.jpg", 0o666)
    # shutil.rmtree(test_root)

if __name__ == "__main__":
    run_test()
