import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# 确保能引入 src 和同级模块
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils import get_global_config_path, get_system_temp_dir, is_admin, set_autostart, check_autostart
from src.cleaner import CacheCleaner


class TestCrossPlatform(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def mock_expanduser(self, path):
        if path.startswith('~'):
            # 将 ~ 替换为临时测试目录，并处理路径分隔符
            return path.replace('~', str(self.temp_path)).replace('/', os.sep)
        return path

    @patch("sys.platform", "linux")
    def test_linux_config_path(self):
        """测试 Linux 下配置路径生成"""
        with patch("os.path.expanduser", side_effect=self.mock_expanduser):
            config_path = get_global_config_path()
            expected = os.path.join(str(self.temp_path), ".config", "software_cache_cleaner")
            self.assertEqual(config_path, expected)
            self.assertTrue(os.path.exists(config_path))

    @patch("sys.platform", "linux")
    def test_linux_system_temp_dir(self):
        """测试 Linux 下的临时目录获取"""
        with patch("tempfile.gettempdir", return_value="/tmp/test_temp"):
            temp_dir = get_system_temp_dir()
            self.assertEqual(temp_dir, "/tmp/test_temp")

    @patch("sys.platform", "linux")
    def test_linux_is_admin(self):
        """测试 Linux 下管理员权限判定"""
        # Windows 的 os 模块没有 getuid，需要指定 create=True 允许 mock 不存在的方法
        with patch("os.getuid", return_value=0, create=True):
            self.assertTrue(is_admin())
        with patch("os.getuid", return_value=1000, create=True):
            self.assertFalse(is_admin())

    @patch("sys.platform", "linux")
    def test_linux_autostart(self):
        """测试 Linux 平台自启动文件的写入与删除"""
        with patch("os.path.expanduser", side_effect=self.mock_expanduser):
            # 开启自启动
            res = set_autostart(True)
            self.assertTrue(res)
            
            desktop_file = self.temp_path / ".config" / "autostart" / "software_cache_cleaner.desktop"
            self.assertTrue(desktop_file.exists())
            
            # 读取内容并验证
            content = desktop_file.read_text(encoding="utf-8")
            self.assertIn("[Desktop Entry]", content)
            self.assertIn("Exec=", content)
            self.assertIn("--auto-clean", content)
            
            # 检查自启动状态
            self.assertTrue(check_autostart())
            
            # 禁用自启动
            res = set_autostart(False)
            self.assertTrue(res)
            self.assertFalse(desktop_file.exists())
            self.assertFalse(check_autostart())

    @patch("sys.platform", "linux")
    def test_linux_cleaner_targets(self):
        """测试 Linux 下 Cleaner 的默认扫描目标"""
        with patch("os.path.expanduser", side_effect=self.mock_expanduser):
            # 预先创建一下路径，确保 cleaner 的 exists() 检查能通过并加入 targets
            mock_var_tmp = self.temp_path / "var_tmp"
            mock_cache = self.temp_path / ".cache"
            mock_trash = self.temp_path / ".local" / "share" / "Trash"
            
            # 模拟系统级 var_tmp 存在
            with patch("pathlib.Path.exists", return_value=True):
                cleaner = CacheCleaner()
                
                # 在 Linux 平台下 targets 会加入这三个路径（对应的绝对路径）
                targets_str = [str(t) for t in cleaner.targets]
                
                # 校验其中包含预留的 /var/tmp 路径以及用户的 .cache 与 Trash 路径
                self.assertTrue(any("var_tmp" in t or "/var/tmp" in t.replace("\\", "/") for t in targets_str))
                self.assertTrue(any(".cache" in t for t in targets_str))
                self.assertTrue(any("Trash" in t for t in targets_str))

    @patch("sys.platform", "linux")
    def test_linux_empty_recycle_bin(self):
        """测试 Linux 平台下的回收站清理动作"""
        with patch("os.path.expanduser", side_effect=self.mock_expanduser):
            # 创建模拟回收站目录
            trash_files = self.temp_path / ".local" / "share" / "Trash" / "files"
            trash_info = self.temp_path / ".local" / "share" / "Trash" / "info"
            
            trash_files.mkdir(parents=True, exist_ok=True)
            trash_info.mkdir(parents=True, exist_ok=True)
            
            # 放入一些待清理的文件和子文件夹
            (trash_files / "test_file.tmp").write_text("dummy")
            sub_dir = trash_files / "sub_folder"
            sub_dir.mkdir()
            (sub_dir / "nested.tmp").write_text("nested")
            
            (trash_info / "test_file.tmp.trashinfo").write_text("info_data")
            
            cleaner = CacheCleaner()
            res = cleaner._empty_recycle_bin()
            
            self.assertEqual(res, 0)
            
            # 确认回收站目录本身还存在，但里面内容已经被清空
            self.assertTrue(trash_files.exists())
            self.assertTrue(trash_info.exists())
            self.assertEqual(len(list(trash_files.iterdir())), 0)
            self.assertEqual(len(list(trash_info.iterdir())), 0)

    @patch("sys.platform", "win32")
    def test_win32_admin_check(self):
        """测试 Windows 平台下的管理员权限检测"""
        mock_ctypes = MagicMock()
        mock_ctypes.windll.shell32.IsUserAnAdmin.return_value = 1
        
        with patch("src.utils.ctypes", mock_ctypes):
            self.assertTrue(is_admin())
            
        mock_ctypes.windll.shell32.IsUserAnAdmin.return_value = 0
        with patch("src.utils.ctypes", mock_ctypes):
            self.assertFalse(is_admin())


if __name__ == "__main__":
    unittest.main()
