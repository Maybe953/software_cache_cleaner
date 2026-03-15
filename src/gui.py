import customtkinter as ctk
import threading
import sys
import os
import json
from tkinter import messagebox, filedialog
from cleaner import CacheCleaner
from utils import format_size, set_autostart, check_autostart, is_admin, get_global_config_path

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class CacheCleanerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("软件缓存清理工具")
        self.geometry("800x700")

        # 将配置和日志上浮至全局目录，无惧跨用户运行与打包位移
        self.application_path = get_global_config_path()
        self.config_path = os.path.join(self.application_path, "config.json")
        self.custom_paths, self.whitelist = self.load_config()

        # 布局配置
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 实时检测管理员状态
        admin_status = " [管理员模式]" if is_admin() else " [普通模式]"
        self.title("软件缓存清理工具" + admin_status)
        
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="软件缓存清理工具" + admin_status, font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(side="left", pady=10)
        
        if not is_admin():
            self.title_label.configure(text_color="gray")

        # 标签页视图
        self.tabview = ctk.CTkTabview(self, width=750)
        self.tabview.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.tabview.add("清理")
        self.tabview.add("设置")
        
        self.setup_clean_tab()
        self.setup_settings_tab()

        # 逻辑状态
        self.cleaner = CacheCleaner(dry_run=True, custom_paths=self.custom_paths, whitelist=self.whitelist)
        self.scan_results = None

        # 检查是否包含自动清理参数
        if "--auto-clean" in sys.argv:
            self.after(1000, self.perform_auto_clean)
        
        # 关机处理程序
        if win32gui:
            self.after(500, self.setup_shutdown_handler)

        # 核心增强：实现“运行一次即激活全员自启动”逻辑 (V4.3)
        if is_admin() and not check_autostart():
            if set_autostart(True):
                self.autostart_var.set(True)
                self.log("[自动激活] 检测到首次管理员运行，已自动为您注册全员自启动任务规划。")

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("custom_paths", []), config.get("whitelist", []) 
            except Exception:
                return [], []
        return [], []

    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "custom_paths": self.custom_paths,
                    "whitelist": self.whitelist
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置失败: {e}", flush=True)

    def setup_shutdown_handler(self):
        try:
            # Get the actual window handle for the tkinter root
            self.hwnd = self.winfo_id()
            self.old_wndproc = win32gui.SetWindowLong(self.hwnd, win32con.GWL_WNDPROC, self.wnd_proc)
        except Exception as e:
            print(f"设置关机处理程序失败: {e}", flush=True)

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_QUERYENDSESSION:
            # If auto-start is enabled, perform cleanup
            if check_autostart():
                c = CacheCleaner(dry_run=False, custom_paths=self.custom_paths, whitelist=self.whitelist)
                c.clean()
            return True
        return win32gui.CallWindowProc(self.old_wndproc, hwnd, msg, wparam, lparam)

    def perform_auto_clean(self):
        self.log("\n[自动执行] 检测到系统启动清理任务，正在处理...")
        self.dry_run_var.set(False)
        self.start_auto_clean_process()

    def start_auto_clean_process(self):
        self.scan_button.configure(state="disabled")
        self.clean_button.configure(state="disabled")
        self.status_bar.start()
        threading.Thread(target=self.run_auto_clean_thread, daemon=True).start()

    def run_auto_clean_thread(self):
        # 传递真实白名单
        self.cleaner = CacheCleaner(dry_run=False, custom_paths=self.custom_paths, whitelist=self.whitelist)
        try:
            self.log(f"\n>>> [V4.1 全域重构版] 引擎已被自动唤醒 <<<")
            self.log(f"[自动清理] 启动成功。")
            self.cleaner.scan(progress_callback=self.progress_callback)
            removed, freed, errors = self.cleaner.clean(progress_callback=self.progress_callback)
            self.log(f"\n[自动清理完成] 已删除: {removed} 个文件, 释放空间: {format_size(freed)}")
        except Exception as e:
            self.log(f"\n[自动清理出错]: {e}")
        self.after(0, self.clean_finished)

    def setup_clean_tab(self):
        tab = self.tabview.tab("清理")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Controls Area
        controls_frame = ctk.CTkFrame(tab)
        controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.scan_button = ctk.CTkButton(controls_frame, text="扫描缓存", command=self.start_scan)
        self.scan_button.pack(side="left", padx=10, pady=10)

        self.clean_button = ctk.CTkButton(controls_frame, text="清理缓存", command=self.start_clean, state="disabled", fg_color="transparent", border_width=2)
        self.clean_button.pack(side="left", padx=10, pady=10)

        self.dry_run_var = ctk.BooleanVar(value=False)
        self.dry_run_switch = ctk.CTkSwitch(controls_frame, text="安全模式 (仅模拟)", variable=self.dry_run_var)
        self.dry_run_switch.pack(side="right", padx=20, pady=10)

        # Log Area
        self.log_textbox = ctk.CTkTextbox(tab, width=600, height=300)
        self.log_textbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.log_textbox.insert("0.0", "准备就绪。\n")

        self.status_bar = ctk.CTkProgressBar(tab)
        self.status_bar.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.status_bar.set(0)

    def setup_settings_tab(self):
        tab = self.tabview.tab("设置")
        
        # General Settings Section
        basic_settings_frame = ctk.CTkFrame(tab)
        basic_settings_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        section_label = ctk.CTkLabel(basic_settings_frame, text="基础设置", font=ctk.CTkFont(size=16, weight="bold"))
        section_label.pack(anchor="w", padx=20, pady=(15, 10))

        # Auto-start switch
        self.autostart_var = ctk.BooleanVar(value=check_autostart())
        self.autostart_switch = ctk.CTkSwitch(
            basic_settings_frame, 
            text="开机自动启动并清理", 
            variable=self.autostart_var,
            command=self.toggle_autostart
        )
        self.autostart_switch.pack(anchor="w", padx=30, pady=10)
        
        info_label = ctk.CTkLabel(
            basic_settings_frame, 
            text="启用后，程序将随系统自动启动，并在开机和关机时执行自动清理。", 
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=600,
            justify="left"
        )
        info_label.pack(anchor="w", padx=30, pady=(0, 15))

        # Custom Paths Section
        custom_paths_frame = ctk.CTkFrame(tab)
        custom_paths_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        path_label = ctk.CTkLabel(custom_paths_frame, text="自定义扫描路径", font=ctk.CTkFont(size=16, weight="bold"))
        path_label.pack(anchor="w", padx=20, pady=(15, 10))

        # Listbox for paths
        self.path_listbox = ctk.CTkTextbox(custom_paths_frame, height=150)
        self.path_listbox.pack(fill="x", padx=20, pady=5)
        self.refresh_path_list()

        # Buttons for path management
        btn_frame = ctk.CTkFrame(custom_paths_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        self.add_path_btn = ctk.CTkButton(btn_frame, text="添加目录", width=100, command=self.add_custom_path)
        self.add_path_btn.pack(side="left", padx=(0, 10))

        self.clear_paths_btn = ctk.CTkButton(btn_frame, text="清空列表", width=100, fg_color="gray", command=self.clear_custom_paths)
        self.clear_paths_btn.pack(side="left")



    def refresh_path_list(self):
        self.path_listbox.configure(state="normal")
        self.path_listbox.delete("0.0", "end")
        if not self.custom_paths:
            self.path_listbox.insert("0.0", "(未添加自定义路径)")
        else:
            for i, path in enumerate(self.custom_paths):
                self.path_listbox.insert("end", f"{i+1}. {path}\n")
        self.path_listbox.configure(state="disabled")

    def add_custom_path(self):
        path = filedialog.askdirectory()
        if path:
            path = os.path.normpath(path)
            if path not in self.custom_paths:
                self.custom_paths.append(path)
                self.save_config()
                self.refresh_path_list()
                # Update cleaner
                self.cleaner = CacheCleaner(dry_run=self.dry_run_var.get(), custom_paths=self.custom_paths, whitelist=self.whitelist)
                self.log(f"已添加自定义路径: {path}")
            else:
                messagebox.showinfo("信息", "该路径已在列表中。")

    def clear_custom_paths(self):
        if self.custom_paths and messagebox.askyesno("确认", "确定清空所有自定义路径吗？"):
            self.custom_paths = []
            self.save_config()
            self.refresh_path_list()
            self.cleaner = CacheCleaner(dry_run=self.dry_run_var.get(), custom_paths=self.custom_paths, whitelist=self.whitelist)
            self.log("已清空所有自定义路径。")

    def toggle_autostart(self):
        enabled = self.autostart_var.get()
        
        # 前置校验：只有管理员权限才能修改计划任务
        if not is_admin():
            messagebox.showwarning("权限受限", "修改自启动设置需要管理员权限。\n\n请右键点击程序，选择“以管理员身份运行”后再试。")
            self.autostart_var.set(not enabled) # 恢复开关状态
            return

        if set_autostart(enabled):
            status = "已开启" if enabled else "已关闭"
            self.log(f"设置：开机自启动及自动清理{status}")
        else:
            messagebox.showerror("错误", "无法修改启动项设置，请检查系统安全软件是否拦截。")
            # 恢复开关状态
            self.autostart_var.set(not enabled)

    def log(self, message):
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")

    def progress_callback(self, *args):
        if len(args) == 1:
            message = args[0]
        elif len(args) == 3:
            message = args[2]
        else:
            return
        self.log(message)

    def start_scan(self):
        self.scan_button.configure(state="disabled")
        self.clean_button.configure(state="disabled")
        self.status_bar.start()
        self.log("\n--- 开始扫描 ---")
        self.log(f"[配置] 当前生效保护名单: {', '.join(self.cleaner.protected_names) if self.cleaner.protected_names else '无'}")
        
        threading.Thread(target=self.run_scan_thread, daemon=True).start()

    def run_scan_thread(self):
        # 传递真正白名单而非空列表
        self.cleaner = CacheCleaner(dry_run=self.dry_run_var.get(), custom_paths=self.custom_paths, whitelist=self.whitelist)
        try:
            self.scan_results = self.cleaner.scan(progress_callback=self.progress_callback)
            total_files = 0
            total_size = 0
            self.log("\n扫描结果：")
            for path, (count, size) in self.scan_results.items():
                self.log(f"- {path}: {count} 个文件, {format_size(size)}")
                total_files += count
                total_size += size
            self.log(f"\n汇总报告: 发现 {total_files} 个文件, 共 {format_size(total_size)}。")
            self.after(0, lambda: self.scan_finished(total_files > 0))
        except Exception as e:
            self.log(f"扫描过程中发生错误: {e}")
            self.after(0, lambda: self.scan_finished(False))

    def scan_finished(self, found_files):
        self.status_bar.stop()
        self.status_bar.set(1)
        self.scan_button.configure(state="normal")
        if found_files:
            self.clean_button.configure(state="normal", fg_color=["#3B8ED0", "#1F6AA5"])
        else:
            self.clean_button.configure(state="disabled", fg_color="transparent")

    def start_clean(self):
        if not self.dry_run_var.get():
            if not messagebox.askyesno("确认删除", "安全模式已关闭。\n确定要永久删除这些文件吗？"):
                return
        
        self.scan_button.configure(state="disabled")
        self.clean_button.configure(state="disabled")
        self.status_bar.start()
        self.log("\n--- 开始清理 ---")
        self.log(f"[配置] 当前生效保护名单: {', '.join(self.cleaner.protected_names) if self.cleaner.protected_names else '无'}")
        
        threading.Thread(target=self.run_clean_thread, daemon=True).start()

    def run_clean_thread(self):
        mode_str = "【正式清理】" if not self.dry_run_var.get() else "【模拟测试】"
        print(f"DEBUG: run_clean_thread -> 模式: {mode_str}", flush=True)
        # 传递真实白名单
        self.cleaner = CacheCleaner(dry_run=self.dry_run_var.get(), custom_paths=self.custom_paths, whitelist=self.whitelist)
        try:
            removed, freed, errors = self.cleaner.clean(progress_callback=self.progress_callback)
            self.log(f"\n清理完成。")
            self.log(f"已删除: {removed} 个文件")
            self.log(f"已释放: {format_size(freed)}")
            if errors:
                self.log(f"\n错误 ({len(errors)}):")
                for err in errors[:5]:
                    self.log(f"- {err}")
                if len(errors) > 5:
                    self.log(f"...以及另外 {len(errors)-5} 个错误。")
        except Exception as e:
            self.log(f"清理过程中发生错误: {e}")
        self.after(0, self.clean_finished)

    def clean_finished(self):
        self.status_bar.stop()
        self.status_bar.set(0)
        self.scan_button.configure(state="normal")
        self.clean_button.configure(state="disabled", fg_color="transparent")

if __name__ == "__main__":
    app = CacheCleanerApp()
    app.mainloop()
