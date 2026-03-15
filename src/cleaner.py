import os
import winreg
from pathlib import Path
from typing import List, Tuple, Dict
from utils import format_size, get_system_temp_dir

class CacheCleaner:
    def __init__(self, dry_run: bool = True, custom_paths: List[str] = None, whitelist: List[str] = None):
        self.dry_run = dry_run
        
        # 恢复由外界（如 config.json）决定的白名单，并叠加硬编码强制保护的底座
        self.protected_names = {'a', 'b'} # 硬编码基础白名单占位符，可修改为实际名称
        if whitelist:
            for w in whitelist:
                if w.strip():
                    self.protected_names.add(w.strip())

        # 硬编码要清理的文件后缀名清单 (V4.2 精准清理版)
        self.target_extensions = {
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
            ".mp4", ".mov", ".avi", ".flv", ".wmv",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".zip", ".rar", ".7z", ".tar", ".gz",
            ".tmp", ".cache"
        }

        # 系统忽略名单 (V3.9)：针对受限的系统项进行静默跳过
        self.system_ignores = {
            'vmware-system', 'vmware-vpx', 'cryptnetdownloadcache', 
            'pnrpcache', 'sclcache', 'system profile', 'local_service', 
            'network_service'
        }
        
        print(f"\n>>> [V4.0 全域清理版] 引擎已就绪 <<<", flush=True)
        print(f">>> 账号保护名单: {list(self.protected_names)}\n", flush=True)
        
        self.targets = []
        self._init_targets(custom_paths)

    def _init_targets(self, custom_paths: List[str] = None):
        # 1. 自定义路径
        if custom_paths:
            for p in custom_paths:
                path_obj = Path(p)
                if path_obj.exists():
                    self.targets.append(path_obj)

        # 2. 系统临时目录
        self.targets.append(Path(get_system_temp_dir()))
        
        # 3. Windows 临时目录
        win_temp = Path(os.environ.get('SystemRoot', 'C:\\Windows')) / 'Temp'
        if win_temp.exists():
            self.targets.append(win_temp)

        # 4. 浏览器缓存 (Chrome / Edge)
        # local_app_data = Path(os.environ.get('LOCALAPPDATA', ''))
        # if local_app_data:
        #     chrome_cache = local_app_data / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'Cache'
        #     if chrome_cache.exists():
        #         self.targets.append(chrome_cache)
            
        #     edge_cache = local_app_data / 'Microsoft' / 'Edge' / 'User Data' / 'Default' / 'Cache'
        #     if edge_cache.exists():
        #         self.targets.append(edge_cache)

        # 5. 企业微信缓存 (WXWorkLocal - 跨用户扫描)
        # 获取系统用户根目录 (确保是 C:\Users 而不是 C:Users)
        sys_drive = os.environ.get('SystemDrive', 'C:')
        if not sys_drive.endswith('\\'):
            sys_drive += '\\'
        users_root = Path(sys_drive) / "Users"
        
        if users_root.exists():
            # 排除列表：系统默认账户、公共账户及隐藏文件
            exclude_users = {'Public', 'Default', 'All Users', 'Default User', 'desktop.ini'}
            
            try:
                for user_dir in os.scandir(users_root):
                    if user_dir.is_dir() and user_dir.name not in exclude_users:
                        user_base_path = Path(user_dir.path)
                        
                        # 1. 企业微信路径 (WXWorkLocal)
                        user_wx_path = user_base_path / "Documents" / "WXWorkLocal"
                        if user_wx_path.exists():
                            self.targets.append(user_wx_path)
                        
                        # 2. 用户临时目录 (Temp)
                        user_temp_path = user_base_path / "AppData" / "Local" / "Temp"
                        if user_temp_path.exists():
                            self.targets.append(user_temp_path)
                        
                        # 3. 用户图片目录 (Pictures)
                        user_pics_path = user_base_path / "Pictures"
                        if user_pics_path.exists():
                            self.targets.append(user_pics_path)

                        # 4. 浏览器默认下载目录 (Downloads)
                        user_dls_path = user_base_path / "Downloads"
                        if user_dls_path.exists():
                            self.targets.append(user_dls_path)
            except Exception:
                # 权限不足或其他 IO 错误，回退到当前用户
                pass

        # 如果通过遍历没找到任何微信路径（或者没权限遍历），尝试当前用户
        if not any(self.is_wx_work(t) for t in self.targets):
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
                    personal_path, _ = winreg.QueryValueEx(key, "Personal")
                    docs_path = Path(os.path.expandvars(personal_path))
                    wx_work_path = docs_path / "WXWorkLocal"
                    if wx_work_path.exists():
                        self.targets.append(wx_work_path)
            except Exception:
                wx_default = Path(os.path.expanduser("~/Documents/WXWorkLocal"))
                if wx_default.exists():
                    self.targets.append(wx_default)
        
        # 路径去重并标准化
        
        clean_targets = []
        seen = set()
        for t in self.targets:
            norm_p = str(t.absolute()).lower()
            if norm_p not in seen:
                seen.add(norm_p)
                clean_targets.append(t)
        self.targets = clean_targets

    def is_wx_work(self, path: Path) -> bool:
        """判定是否为企业微信路径 (不区分大小写)"""
        return "wxworklocal" in str(path).lower()

    def scan(self, progress_callback=None) -> Dict[str, Tuple[int, int]]:
        results = {}
        for target in self.targets:
            if not target.exists():
                continue
            
            # 如果起始目录本身就是受保护的名称（例如自定义路径添加了受保护的账号文件夹）
            # [Old Case-Insensitive] if target.name.lower() in self.protected_names:
            if target.name in self.protected_names:
                if progress_callback:
                    progress_callback(f"  [扫描跳过] 绝对保护项 (名称匹配): {target.name}")
                continue

            if progress_callback:
                progress_callback(f"正在扫描 {target}...")

            count = 0
            size = 0
            
            # 系统扫描逻辑
            try:
                # 使用 os.walk 并通过修改 dirnames 实现“不进入”指定目录
                for root, dirnames, filenames in os.walk(target):
                    # 关键操作：原地修改 dirnames，过滤掉受保护的文件夹名
                    # 这样 os.walk 就绝对不会进入这些文件夹
                    original_dirs = list(dirnames)
                    for d in original_dirs:
                        d_lower = d.lower()
                        # [Old Case-Insensitive]
                        # if d_lower in self.protected_names or d_lower in self.system_ignores:
                        #     if progress_callback:
                        #         notify_type = "绝对隔离" if d_lower in self.protected_names else "系统保护"
                        #         progress_callback(f"    [{notify_type}] 排除项: {d}")
                        #     dirnames.remove(d)

                        # [New Strict Case]
                        if d in self.protected_names or d_lower in self.system_ignores:
                            if progress_callback:
                                notify_type = "绝对隔离" if d in self.protected_names else "系统保护"
                                progress_callback(f"    [{notify_type}] 排除项: {d}")
                            dirnames.remove(d)
                    
                    # 遍历目录及文件清单
                    
                    for file in filenames:
                        try:
                            f_path = Path(root) / file
                            
                            # 判定是否在过滤后缀清单中
                            if f_path.suffix.lower() in self.target_extensions:
                                size += f_path.stat().st_size
                                count += 1
                        except (PermissionError, OSError):
                            continue
            except (PermissionError, OSError):
                pass
            
            results[str(target)] = (count, size)
        return results

    def clean(self, progress_callback=None) -> Tuple[int, int, List[str]]:
        print(f"DEBUG: [清除任务启动] dry_run: {self.dry_run}, 生效保护名单: {list(self.protected_names)}")
        files_removed = 0
        bytes_freed = 0
        errors = []

        for target in self.targets:
            if not target.exists():
                continue

            # 如果起始目录本身就匹配保护名
            # [Old Case-Insensitive] if target.name.lower() in self.protected_names:
            if target.name in self.protected_names:
                if progress_callback:
                    progress_callback(0, 0, f"  [跳过清理] 绝对保护项: {target.name}")
                continue

            if progress_callback:
                progress_callback(0, 0, f"正在清理 {target}...")

            # 递归删除逻辑，内部会再次检查保护名单
            removed, freed, errs = self._recursive_delete(target)
            files_removed += removed
            bytes_freed += freed
            errors.extend(errs)
        
        return files_removed, bytes_freed, errors

    def _recursive_delete(self, path: Path) -> Tuple[int, int, List[str]]:
        """
        地毯式递归深度清理：根据后缀清单删除文件，保留文件夹结构。
        """
        removed, freed = 0, 0
        errors = []

        if not path.exists():
            return 0, 0, []

        try:
            # os.scandir 比 Path.glob 更快更稳定
            for entry in os.scandir(path):
                entry_path = Path(entry.path)
                
                # 综合过滤：只要名字匹配名单，绝对不动
                if entry_path.name in self.protected_names or entry_path.name.lower() in self.system_ignores:
                    continue

                try:
                    if entry.is_file() or entry.is_symlink():
                        # 精准后缀匹配：只删除命中后缀的文件
                        if entry_path.suffix.lower() in self.target_extensions:
                            size = entry.stat().st_size
                            if not self.dry_run:
                                try:
                                    entry_path.unlink()
                                    removed += 1
                                    freed += size
                                except (PermissionError, OSError):
                                    pass
                            else:
                                removed += 1
                                freed += size
                            
                    elif entry.is_dir():
                        # 继续向下穿透扫描全量目录
                        r, f, e = self._recursive_delete(entry_path)
                        removed += r
                        freed += f
                        errors.extend(e)
                except Exception as e:
                    errors.append(f"访问项出错 {entry.name}: {e}")

            # 目录收尾：不再删除任何文件夹，保留目录结构便于软件运行
            pass

        except Exception as e:
            errors.append(f"处理目录 {path} 出错: {e}")

        return removed, freed, errors
