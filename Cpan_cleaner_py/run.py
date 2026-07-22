"""推荐在 PyCharm 中直接运行这个文件，也作为 PyInstaller 打包入口。"""

from __future__ import annotations

import sys
from pathlib import Path


if __package__:
    from .app import main
else:
    # 兼容两种场景：
    # 1. PyCharm 直接运行 Cpan_cleaner_py/run.py，此时 app.py 在同目录；
    # 2. PyInstaller 分析入口脚本时，需要项目根目录可导入 Cpan_cleaner_py。
    current_dir = Path(__file__).resolve().parent
    project_dir = current_dir.parent
    for item in (str(current_dir), str(project_dir)):
        if item not in sys.path:
            sys.path.insert(0, item)
    try:
        from Cpan_cleaner_py.app import main
    except ModuleNotFoundError:
        from app import main


if __name__ == "__main__":
    main()