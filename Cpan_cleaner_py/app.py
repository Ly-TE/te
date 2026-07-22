"""
 C 盘清理工具

界面结构尽量贴近常见清理软件：左侧功能菜单，右侧扫描/清理列表。
已实现：
- 首页概览
- 基础清理
- 系统清理
- 软件清理
- 用户清理
- 大文件扫描
- 工具箱

运行：python -m Cpan_cleaner_py.app
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, TOP, Listbox, StringVar, Tk, filedialog, messagebox
from tkinter import ttk
from typing import Callable, Iterable, Optional


APP_NAME = " C 盘清理工具"
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent


def get_writable_app_dir() -> Path:
    """获取可写的应用数据目录。

    源码运行时优先使用项目 logs 目录，便于开发调试；
    exe 运行时不要写入 PyInstaller 的 _internal/Program Files 目录，
    否则普通用户权限下会 PermissionError。
    """
    if getattr(sys, "frozen", False):
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "MozhenCleanerPy"
    return PROJECT_DIR / "logs"


LOG_DIR = get_writable_app_dir()
LOG_FILE = LOG_DIR / "Cpan_cleaner_py.log"


def setup_logger() -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger("Cpan_cleaner_py")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
    return logger


LOGGER = setup_logger()


def is_admin() -> bool:
    """判断管理员权限。

    这里故意不使用 ctypes：当前项目根目录中含有旧打包程序的 python310.dll，
    Anaconda 等环境导入 ctypes 时可能发生 DLL 版本冲突。使用系统命令更稳妥。
    """
    try:
        completed = subprocess.run(
            ["net", "session"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        return completed.returncode == 0
    except Exception:
        return False


def format_size(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{size} B"


def safe_resolve(path: Path) -> Optional[Path]:
    try:
        return path.expanduser().resolve(strict=False)
    except OSError:
        return None


@dataclass
class CleanTarget:
    category: str
    name: str
    path: Path
    description: str
    selected: bool = True
    min_age_hours: int = 0
    suffixes: Optional[set[str]] = None
    recursive: bool = True
    min_file_size: int = 0
    size: int = 0
    file_count: int = 0
    errors: list[str] = field(default_factory=list)


class CleanerEngine:
    def __init__(self) -> None:
        self.system_drive = Path(os.environ.get("SystemDrive", "C:"))
        self.user_profile = Path(os.environ.get("USERPROFILE", str(Path.home())))
        self.windows_dir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        self.local_app_data = Path(os.environ.get("LOCALAPPDATA", self.user_profile / "AppData" / "Local"))
        self.app_data = Path(os.environ.get("APPDATA", self.user_profile / "AppData" / "Roaming"))

    def categories(self) -> list[str]:
        return ["首页概览", "基础清理", "系统清理", "软件清理", "用户清理", "大文件扫描", "工具箱"]

    def default_targets(self) -> list[CleanTarget]:
        tmp_suffixes = {".tmp", ".temp", ".log", ".old", ".bak", ".dmp", ".chk"}
        browser_roots = [
            ("Edge 缓存", self.local_app_data / "Microsoft" / "Edge" / "User Data"),
            ("Chrome 缓存", self.local_app_data / "Google" / "Chrome" / "User Data"),
            ("360/Chromium 缓存", self.local_app_data / "Chromium" / "User Data"),
        ]
        targets = [
            CleanTarget("基础清理", "用户临时文件", Path(tempfile.gettempdir()), "当前用户 Temp 目录", True, 2),
            CleanTarget("基础清理", "崩溃转储", self.local_app_data / "CrashDumps", "应用崩溃产生的 dmp 文件", True, 0),
            CleanTarget("基础清理", "最近临时文件", self.user_profile / "AppData" / "Local" / "Temp", "用户临时缓存", True, 2),

            CleanTarget("系统清理", "Windows 临时文件", self.windows_dir / "Temp", "系统 Temp，建议管理员运行", True, 24),
            CleanTarget("系统清理", "Windows 更新缓存", self.windows_dir / "SoftwareDistribution" / "Download", "系统更新下载缓存；更新中勿清理", False, 24),
            CleanTarget("系统清理", "缩略图/图标缓存", self.local_app_data / "Microsoft" / "Windows" / "Explorer", "资源管理器图标与缩略图缓存", False, 24, {".db"}),
            CleanTarget("系统清理", "错误报告 WER", self.app_data / "Microsoft" / "Windows" / "WER", "Windows 错误报告队列/归档", True, 0),
            CleanTarget("系统清理", "Prefetch 预读取", self.windows_dir / "Prefetch", "预读取缓存，会自动重建", False, 168, {".pf"}),
            CleanTarget("系统清理", "C 盘回收站", self.system_drive / "$Recycle.Bin", "回收站文件，删除后不可恢复", False, 0),
        ]
        for name, root in browser_roots:
            targets.extend([
                CleanTarget("软件清理", name, root, "Chromium 内核浏览器 Cache/Code Cache/GPUCache", True, 2),
            ])
        targets.extend([
            CleanTarget("软件清理", "Firefox 缓存", self.local_app_data / "Mozilla" / "Firefox" / "Profiles", "Firefox profile cache2 缓存", True, 2),
            CleanTarget("软件清理", "微信缓存", self.user_profile / "Documents" / "WeChat Files", "微信文件目录中的 Cache/Temp，仅扫描匹配目录", False, 24),
            CleanTarget("软件清理", "QQ/TIM 缓存", self.user_profile / "Documents" / "Tencent Files", "腾讯聊天软件缓存，仅扫描匹配目录", False, 24),

            CleanTarget("用户清理", "下载目录临时安装包", self.user_profile / "Downloads", "仅匹配临时/安装/日志后缀", False, 168, tmp_suffixes | {".msi", ".crdownload"}),
            CleanTarget("用户清理", "桌面临时文件", self.user_profile / "Desktop", "仅匹配 tmp/log/dmp/bak 等后缀", False, 168, tmp_suffixes),
            CleanTarget("用户清理", "文档临时文件", self.user_profile / "Documents", "仅匹配 tmp/log/dmp/bak 等后缀", False, 168, tmp_suffixes),

            CleanTarget("大文件扫描", "用户目录大文件", self.user_profile, "扫描用户目录中超过 100MB 的文件；默认不勾选", False, 0, None, True, 100 * 1024 * 1024),
            CleanTarget("大文件扫描", "下载目录大文件", self.user_profile / "Downloads", "扫描下载目录中超过 100MB 的文件；默认不勾选", False, 0, None, True, 100 * 1024 * 1024),
        ])
        return [target for target in targets if self.is_allowed_target(target.path)]

    def is_allowed_target(self, path: Path) -> bool:
        resolved = safe_resolve(path)
        if resolved is None:
            return False
        dangerous = [
            self.system_drive.resolve(strict=False),
            self.windows_dir.resolve(strict=False),
            Path(r"C:\Program Files").resolve(strict=False),
            Path(r"C:\Program Files (x86)").resolve(strict=False),
            Path(r"C:\Users").resolve(strict=False),
        ]
        return all(resolved != item for item in dangerous)

    def _special_roots(self, target: CleanTarget) -> list[Path]:
        if target.name in {"Edge 缓存", "Chrome 缓存", "360/Chromium 缓存"}:
            patterns = ["Default/Cache", "Default/Code Cache", "Default/GPUCache", "*/Cache", "*/Code Cache", "*/GPUCache"]
            return [p for pattern in patterns for p in target.path.glob(pattern) if p.exists()]
        if target.name == "Firefox 缓存":
            return [p / "cache2" for p in target.path.iterdir() if p.is_dir()] if target.path.exists() else []
        if target.name in {"微信缓存", "QQ/TIM 缓存"}:
            names = {"cache", "temp", "tmp", "caches", "filecache"}
            return [p for p in target.path.rglob("*") if p.is_dir() and p.name.lower() in names] if target.path.exists() else []
        return [target.path]

    def iter_cleanable_files(self, target: CleanTarget) -> Iterable[Path]:
        if not target.path.exists():
            return
        now = time.time()
        min_age = target.min_age_hours * 3600
        for root in self._special_roots(target):
            if not root.exists() or not self.is_allowed_target(root):
                continue
            walker = os.walk(root, onerror=lambda e: target.errors.append(str(e))) if target.recursive else [(str(root), [], os.listdir(root))]
            for current_root, dir_names, file_names in walker:
                current = Path(current_root)
                if not self.is_allowed_target(current):
                    dir_names[:] = []
                    continue
                for file_name in file_names:
                    file_path = current / file_name
                    try:
                        if not file_path.is_file():
                            continue
                        stat = file_path.stat()
                        if min_age and now - stat.st_mtime < min_age:
                            continue
                        if target.suffixes is not None and file_path.suffix.lower() not in target.suffixes:
                            continue
                        if target.min_file_size and stat.st_size < target.min_file_size:
                            continue
                        yield file_path
                    except (PermissionError, FileNotFoundError, OSError) as exc:
                        target.errors.append(f"{file_path}: {exc}")

    def scan(self, targets: list[CleanTarget], progress: Optional[Callable[[CleanTarget, int, int], None]] = None) -> None:
        total_targets = len(targets)
        for index, target in enumerate(targets, start=1):
            target.size = 0
            target.file_count = 0
            target.errors.clear()
            if not target.path.exists():
                target.errors.append("目录不存在")
                if progress:
                    progress(target, index, total_targets)
                continue
            for file_path in self.iter_cleanable_files(target):
                try:
                    target.size += file_path.stat().st_size
                    target.file_count += 1
                except OSError as exc:
                    target.errors.append(f"{file_path}: {exc}")
            LOGGER.info("扫描 %s/%s：%s，%s 个文件", target.category, target.name, format_size(target.size), target.file_count)
            if progress:
                progress(target, index, total_targets)

    def clean(self, targets: list[CleanTarget], dry_run: bool = False) -> tuple[int, int, list[str]]:
        total_size = 0
        total_count = 0
        errors: list[str] = []
        for target in targets:
            if not target.selected or not target.path.exists():
                continue
            for file_path in list(self.iter_cleanable_files(target)):
                try:
                    size = file_path.stat().st_size
                    if not dry_run:
                        file_path.unlink(missing_ok=True)
                    total_size += size
                    total_count += 1
                except (PermissionError, FileNotFoundError, OSError) as exc:
                    errors.append(f"{file_path}: {exc}")
            if not dry_run:
                self.remove_empty_dirs(target.path)
        LOGGER.info("%s：%s，%s 个文件，错误 %s 个", "试运行" if dry_run else "清理", format_size(total_size), total_count, len(errors))
        return total_size, total_count, errors

    def remove_empty_dirs(self, root: Path) -> None:
        if not root.exists() or not self.is_allowed_target(root):
            return
        for current_root, dir_names, _ in os.walk(root, topdown=False):
            for dir_name in dir_names:
                directory = Path(current_root) / dir_name
                try:
                    if self.is_allowed_target(directory):
                        directory.rmdir()
                except OSError:
                    pass


class CleanerApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.engine = CleanerEngine()
        self.targets = self.engine.default_targets()
        self.current_category = "首页概览"
        self.busy = False
        self.status = StringVar(value="请在左侧选择功能，先扫描，再清理。")
        self.build_ui()
        self.show_category("首页概览")

    def build_ui(self) -> None:
        self.root.title(f"{APP_NAME} - PyCharm 源码版")
        self.root.geometry("1180x720")
        self.root.minsize(980, 600)

        top = ttk.Frame(self.root, padding=10)
        top.pack(side=TOP, fill="x")
        ttk.Label(top, text=APP_NAME, font=("Microsoft YaHei UI", 18, "bold")).pack(side=LEFT)
        ttk.Label(top, text=f"权限：{'管理员' if is_admin() else '普通用户'}").pack(side=RIGHT)

        main = ttk.Frame(self.root)
        main.pack(fill=BOTH, expand=True)

        left = ttk.Frame(main, width=180, padding=(10, 0, 8, 10))
        left.pack(side=LEFT, fill="y")
        ttk.Label(left, text="功能菜单", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        self.menu = Listbox(left, height=16, activestyle="none", exportselection=False, font=("Microsoft YaHei UI", 10))
        for item in self.engine.categories():
            self.menu.insert(END, item)
        self.menu.pack(fill="y", expand=True)
        self.menu.selection_set(0)
        self.menu.bind("<<ListboxSelect>>", self.on_menu_select)

        right = ttk.Frame(main, padding=(0, 0, 10, 10))
        right.pack(side=RIGHT, fill=BOTH, expand=True)

        toolbar = ttk.Frame(right)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(toolbar, text="开始扫描", command=self.scan_current_async).pack(side=LEFT, padx=3)
        ttk.Button(toolbar, text="扫描全部含大文件", command=lambda: self.scan_async(self.targets)).pack(side=LEFT, padx=3)
        ttk.Button(toolbar, text="试运行", command=lambda: self.clean_current_async(True)).pack(side=LEFT, padx=3)
        ttk.Button(toolbar, text="开始清理", command=lambda: self.clean_current_async(False)).pack(side=LEFT, padx=3)
        ttk.Button(toolbar, text="添加自定义目录", command=self.add_custom_target).pack(side=LEFT, padx=3)
        ttk.Button(toolbar, text="打开日志", command=lambda: os.startfile(str(LOG_FILE))).pack(side=LEFT, padx=3)

        self.summary = ttk.Label(right, text="", font=("Microsoft YaHei UI", 10))
        self.summary.pack(fill="x", pady=(0, 6))

        columns = ("checked", "category", "name", "path", "size", "files", "age", "description")
        self.tree = ttk.Treeview(right, columns=columns, show="headings")
        headings = {"checked": "清理", "category": "分类", "name": "项目", "path": "路径", "size": "大小", "files": "文件数", "age": "保留", "description": "说明"}
        widths = {"checked": 55, "category": 85, "name": 150, "path": 310, "size": 100, "files": 70, "age": 80, "description": 260}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<Double-1>", self.toggle_selected)

        bottom = ttk.Frame(right, padding=(0, 8, 0, 0))
        bottom.pack(fill="x")
        ttk.Label(bottom, textvariable=self.status).pack(side=LEFT)
        ttk.Button(bottom, text="全选当前", command=lambda: self.set_current(True)).pack(side=RIGHT, padx=3)
        ttk.Button(bottom, text="全不选当前", command=lambda: self.set_current(False)).pack(side=RIGHT, padx=3)

    def on_menu_select(self, _event=None) -> None:
        selection = self.menu.curselection()
        if selection:
            self.show_category(self.menu.get(selection[0]))

    def visible_targets(self) -> list[CleanTarget]:
        if self.current_category == "首页概览":
            return self.targets
        if self.current_category == "工具箱":
            return []
        return [target for target in self.targets if target.category == self.current_category]

    def show_category(self, category: str) -> None:
        self.current_category = category
        if category == "工具箱":
            self.show_toolbox()
            return
        self.refresh_table()

    def refresh_table(self) -> None:
        self.tree.delete(*self.tree.get_children())
        targets = self.visible_targets()
        for target in targets:
            index = self.targets.index(target)
            self.tree.insert("", END, iid=str(index), values=(
                "✓" if target.selected else "",
                target.category,
                target.name,
                str(target.path),
                format_size(target.size),
                target.file_count,
                f"{target.min_age_hours}h",
                target.description,
            ))
        total = sum(t.size for t in targets)
        count = sum(t.file_count for t in targets)
        self.summary.config(text=f"当前功能：{self.current_category} | 项目 {len(targets)} 个 | 已扫描 {format_size(total)} / {count} 个文件")
        self.status.set("双击列表行可切换是否清理；大文件扫描默认不勾选，请谨慎处理。")

    def show_toolbox(self) -> None:
        self.tree.delete(*self.tree.get_children())
        tools = [
            ("打开用户 Temp", Path(tempfile.gettempdir())),
            ("打开 Windows Temp", self.engine.windows_dir / "Temp"),
            ("打开下载目录", self.engine.user_profile / "Downloads"),
            ("打开日志目录", LOG_DIR),
            ("启动磁盘清理 cleanmgr", None),
        ]
        for i, (name, path) in enumerate(tools):
            self.tree.insert("", END, iid=f"tool-{i}", values=("", "工具箱", name, str(path or "系统命令"), "", "", "", "双击执行"))
        self.summary.config(text="工具箱：双击工具项执行。")
        self.status.set("工具箱不会直接删除文件。")

    def toggle_selected(self, _event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        iid = selected[0]
        if iid.startswith("tool-"):
            self.run_tool(iid)
            return
        target = self.targets[int(iid)]
        target.selected = not target.selected
        self.refresh_table()

    def run_tool(self, iid: str) -> None:
        idx = int(iid.split("-")[1])
        if idx == 0:
            os.startfile(tempfile.gettempdir())
        elif idx == 1:
            os.startfile(str(self.engine.windows_dir / "Temp"))
        elif idx == 2:
            os.startfile(str(self.engine.user_profile / "Downloads"))
        elif idx == 3:
            LOG_DIR.mkdir(exist_ok=True)
            os.startfile(str(LOG_DIR))
        elif idx == 4:
            subprocess.Popen(["cleanmgr.exe"], shell=False)

    def scan_current_async(self) -> None:
        targets = self.targets if self.current_category == "首页概览" else self.visible_targets()
        if self.current_category == "首页概览":
            # 首页默认不扫描“大文件扫描”，避免管理员启动后遍历整个用户目录耗时很久，
            # 导致用户误以为“没有开始”。需要查大文件时请进入左侧“大文件扫描”。
            targets = [target for target in targets if target.category != "大文件扫描"]
        if not targets:
            self.status.set("当前功能没有可扫描项目。")
            return
        self.scan_async(targets)

    def scan_async(self, targets: list[CleanTarget]) -> None:
        if self.busy:
            self.status.set("已有任务正在执行，请等待完成。")
            return
        self.run_worker(lambda: self.scan(targets))

    def scan(self, targets: list[CleanTarget]) -> None:
        self.root.after(0, lambda: self.status.set("正在扫描，请稍候..."))

        def on_progress(target: CleanTarget, index: int, total: int) -> None:
            self.root.after(0, self.refresh_table)
            self.root.after(
                0,
                lambda: self.status.set(
                    f"正在扫描 {index}/{total}：{target.category} / {target.name}，"
                    f"已发现 {format_size(target.size)}，{target.file_count} 个文件"
                ),
            )

        self.engine.scan(targets, on_progress)
        self.root.after(0, self.refresh_table)
        self.root.after(0, lambda: self.status.set("扫描完成。若需查找大文件，请单独进入左侧“大文件扫描”。"))

    def clean_current_async(self, dry_run: bool) -> None:
        if self.busy:
            self.status.set("已有任务正在执行，请等待完成。")
            return
        targets = [t for t in (self.targets if self.current_category == "首页概览" else self.visible_targets()) if t.selected]
        if not targets:
            messagebox.showwarning("未选择项目", "请先勾选需要处理的项目。")
            return
        if not dry_run and not messagebox.askyesno("确认清理", "将删除所选项目中的可清理文件，删除后通常不可恢复。是否继续？"):
            return
        self.run_worker(lambda: self.clean(targets, dry_run))

    def clean(self, targets: list[CleanTarget], dry_run: bool) -> None:
        self.root.after(0, lambda: self.status.set("正在试运行..." if dry_run else "正在清理..."))
        size, count, errors = self.engine.clean(targets, dry_run)
        self.engine.scan(targets)
        self.root.after(0, self.refresh_table)
        msg = f"{'试运行' if dry_run else '清理'}完成：{count} 个文件，{format_size(size)}，错误 {len(errors)} 个。"
        self.root.after(0, lambda: self.status.set(msg))
        if errors:
            for err in errors[:50]:
                LOGGER.warning(err)
            self.root.after(0, lambda: messagebox.showinfo("部分文件未处理", f"有 {len(errors)} 个文件未处理，详情见日志：\n{LOG_FILE}"))

    def set_current(self, selected: bool) -> None:
        for target in self.visible_targets():
            target.selected = selected
        self.refresh_table()

    def add_custom_target(self) -> None:
        folder = filedialog.askdirectory(title="选择自定义清理目录")
        if not folder:
            return
        path = Path(folder)
        if not self.engine.is_allowed_target(path):
            messagebox.showerror("不允许的目录", "为避免误删，不允许直接选择 C 盘根目录、Windows、Program Files、C:\\Users 等危险路径。")
            return
        self.targets.append(CleanTarget("用户清理", "自定义目录", path, "用户添加目录，默认保留 24 小时内文件", False, 24))
        self.current_category = "用户清理"
        self.refresh_table()

    def run_worker(self, func: Callable[[], None]) -> None:
        self.busy = True
        def wrapped() -> None:
            try:
                func()
            except Exception as exc:
                LOGGER.exception("任务异常")
                self.root.after(0, lambda: messagebox.showerror("错误", str(exc)))
            finally:
                self.busy = False
        threading.Thread(target=wrapped, daemon=True).start()


def main() -> None:
    root = Tk()
    try:
        root.call("tk", "scaling", 1.15)
    except Exception:
        pass
    CleanerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
