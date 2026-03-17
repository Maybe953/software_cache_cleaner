import os
import sys
import argparse
import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

# 关键：处理打包环境下的路径，确保能找到同级模块
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后的临时解压目录
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    # 源代码在打包文件内部的相对位置（根据 --add-data "src;src"）
    src_dir = os.path.join(base_dir, 'src')
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
else:
    # 正常开发环境
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

from cleaner import CacheCleaner
from utils import format_size, get_global_config_path, is_admin, check_autostart, set_autostart

console = Console()

def main():
    parser = argparse.ArgumentParser(description="软件缓存清理工具")
    parser.add_argument("--scan", action="store_true", help="扫描缓存文件")
    parser.add_argument("--clean", action="store_true", help="清理缓存文件")
    parser.add_argument("--dry-run", action="store_true", default=False, help="安全模式 (仅模拟)")
    parser.add_argument("--force", action="store_true", help="强制删除 (禁用模拟模式)")
    parser.add_argument("--auto-clean", action="store_true", help="开机自动清理模式")
    
    args = parser.parse_args()

    # [自动部署逻辑已禁用]：不再开机即导出自启动，改为完全由用户手动在设置中开启
    # if is_admin() and not check_autostart():
    #     set_autostart(True)

    # 如果没有任何参数，或者带了 --auto-clean 参数（由计划任务调用），我们启动 GUI
    if len(sys.argv) == 1 or args.auto_clean:
        try:
            from .gui import CacheCleanerApp
        except ImportError:
            from gui import CacheCleanerApp
        
        app = CacheCleanerApp()
        app.mainloop()
        return

    # Determine global application path for config and logs
    global_app_path = get_global_config_path()
    config_path = os.path.join(global_app_path, "config.json")
    custom_paths, whitelist = [], []
    
    if os.path.exists(config_path):
        try:
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                custom_paths = config.get("custom_paths", [])
                whitelist = config.get("whitelist", [])
        except Exception:
            pass

    # Determine mode
    dry_run = False
    if args.dry_run:
        dry_run = True
    elif args.force:
        dry_run = False

    cleaner = CacheCleaner(dry_run=dry_run, custom_paths=custom_paths, whitelist=whitelist)
    
    if args.scan or args.clean:
        total_size = 0
        total_files = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="正在扫描目录...", total=None)
            scan_results = cleaner.scan()

        table = Table(title="扫描结果")
        table.add_column("目录", style="cyan", no_wrap=True)
        table.add_column("文件数", justify="right", style="magenta")
        table.add_column("大小", justify="right", style="green")

        for path, (count, size) in scan_results.items():
            table.add_row(
                path,
                str(count),
                format_size(size)
            )
            total_size += size
            total_files += count

        console.print(table)
        console.print(f"\n[bold]汇总:[/bold] {total_files} 个文件, 共 {format_size(total_size)}\n")

    if args.clean:
        if dry_run:
            console.print("[yellow]模拟模式：不会删除任何文件。[/yellow]")
            console.print("请添加 [bold]--clean[/bold] 或 [bold]--force[/bold] 运行以执行实际删除。")
        else:
            if Confirm.ask(f"确定要删除 {total_files} 个文件（占用空间 {format_size(total_size)}）吗？"):
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=True,
                ) as progress:
                    progress.add_task(description="正在清理...", total=None)
                    removed_count, freed_bytes, errors = cleaner.clean()
                
                console.print(f"[bold green]清理完成！[/bold green]")
                console.print(f"已移除: {removed_count} 个文件")
                console.print(f"已释放: {format_size(freed_bytes)}")
                
                if errors:
                    console.print(f"\n[bold red]遇到错误 ({len(errors)}):[/bold red]")
                    for err in errors[:5]: # Show first 5 errors
                        console.print(f"- {err}")
                    if len(errors) > 5:
                        console.print(f"... 以及另外 {len(errors) - 5} 个错误。")
                    
                    # Log errors to global file for headless execution review
                    try:
                        log_path = os.path.join(global_app_path, "cleaner_errors.log")
                        with open(log_path, "a", encoding="utf-8") as lf:
                            lf.write(f"\n--- [Auto Clean Errors {datetime.datetime.now()}] ---\n")
                            for err in errors:
                                lf.write(f"{err}\n")
                    except Exception:
                        pass

if __name__ == "__main__":
    main()
