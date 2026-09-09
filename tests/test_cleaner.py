import os
import shutil
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.cleaner import CacheCleaner

def test_cleaner_mock():
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create mock directories
        mock_temp = temp_path / "MockTemp"
        mock_chrome = temp_path / "MockChrome" / "Cache"
        mock_temp.mkdir(parents=True)
        mock_chrome.mkdir(parents=True)
        
        # Create dummy files
        (mock_temp / "file1.tmp").write_text("content")
        (mock_temp / "file2.tmp").write_text("content" * 100)
        (mock_chrome / "cache_data.cache").write_text("cache" * 50)
        
        print(f"Created mock environment at {temp_dir}")
        
        # Initialize Cleaner with mock targets
        cleaner = CacheCleaner(dry_run=True)
        # Override targets for testing
        cleaner.targets = [mock_temp, mock_chrome]
        
        # Test Scan
        print("\n--- Testing Scan ---")
        scan_results = cleaner.scan()
        total_files = 0
        for path, (count, size) in scan_results.items():
            print(f"Path: {path} | Files: {count} | Size: {size}")
            total_files += count
        
        if total_files == 3:
            print("Scan Verification: PASSED")
        else:
            print(f"Scan Verification: FAILED (Expected 3, got {total_files})")
            return

        # Test Clean (Dry Run)
        print("\n--- Testing Clean (Dry Run) ---")
        removed, freed, errors = cleaner.clean()
        print(f"Dry Run Removed: {removed}")
        
        if removed == 3 and (mock_temp / "file1.tmp").exists():
             print("Dry Run Verification: PASSED")
        else:
             print(f"Dry Run Verification: FAILED (Removed: {removed}, Exists: {(mock_temp / 'file1.tmp').exists()})")
             return

        # Test Clean (Real)
        print("\n--- Testing Clean (Real) ---")
        cleaner.dry_run = False
        removed, freed, errors = cleaner.clean()
        print(f"Real Clean Removed: {removed}")
        
        remaining_files = list(mock_temp.glob("*")) + list(mock_chrome.glob("*"))
        if removed == 3 and len(remaining_files) == 0:
             print("Real Clean Verification: PASSED")
        else:
             print(f"Real Clean Verification: FAILED (Remaining files: {len(remaining_files)})")

if __name__ == "__main__":
    test_cleaner_mock()
