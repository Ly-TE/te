# 磨针 C 盘清理工具 - PyCharm 源码目录版

本目录将源码集中放置，便于在 PyCharm 中打开、运行和二次开发。

## 运行

推荐在 PyCharm 中直接运行：

```bash
Cpan_cleaner_py/run.py
```

或在项目根目录执行：

```bash
python run_mozhen_cleaner.py
```

不建议使用 Anaconda 在项目根目录直接运行 `python -m mozhen_cleaner_py.app`，因为当前目录包含旧版打包程序释放出的 `python310.dll`，可能与 Anaconda 的 Python 版本冲突。

## 左侧菜单功能

- **首页概览**：显示全部清理项目，支持扫描全部、试运行、清理。
- **基础清理**：用户 Temp、崩溃转储、常规临时文件。
- **系统清理**：Windows Temp、更新缓存、缩略图缓存、错误报告、Prefetch、回收站。
- **软件清理**：Edge、Chrome、Chromium/360、Firefox、微信、QQ/TIM 等常见软件缓存。
- **用户清理**：下载、桌面、文档中的临时文件，也可添加自定义目录。
- **大文件扫描**：扫描用户目录/下载目录中超过 100MB 的大文件，默认不勾选，避免误删。
- **工具箱**：打开 Temp、下载、日志目录，启动系统磁盘清理工具 `cleanmgr.exe`。

## 安全策略

- 默认先扫描预览，不会启动即删除。
- 清理前需要二次确认。
- 大文件、回收站、更新缓存等高风险项目默认不勾选。
- 禁止直接选择 `C:\`、`C:\Windows`、`C:\Program Files`、`C:\Program Files (x86)`、`C:\Users` 等危险目录。
- 删除失败、权限不足等信息会写入 `logs/mozhen_cleaner_py.log`。
