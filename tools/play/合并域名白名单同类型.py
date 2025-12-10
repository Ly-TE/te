import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
import threading
import re
import os
from datetime import datetime


class DomainExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("域名根域名提取工具")
        self.root.geometry("900x700")

        # 存储状态变量
        self.files_to_process = []
        self.all_root_domains = set()
        self.is_processing = False

        # 设置样式
        self.setup_styles()

        # 创建界面
        self.create_widgets()

    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.configure('Title.TLabel', font=('微软雅黑', 14, 'bold'))
        style.configure('SubTitle.TLabel', font=('微软雅黑', 11, 'bold'))
        style.configure('Status.TLabel', font=('微软雅黑', 10))

    def create_widgets(self):
        """创建所有界面组件"""

        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="域名根域名提取工具", style='Title.TLabel')
        title_label.pack(pady=(0, 20))

        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding="15")
        file_frame.pack(fill=tk.X, pady=(0, 15))

        # 文件列表
        file_list_frame = ttk.Frame(file_frame)
        file_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        ttk.Label(file_list_frame, text="待处理文件列表:", font=('微软雅黑', 10)).pack(anchor=tk.W)

        # 创建带滚动条的文件列表
        file_list_container = ttk.Frame(file_list_frame)
        file_list_container.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # 滚动条
        scrollbar = tk.Scrollbar(file_list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 文件列表框
        self.file_listbox = tk.Listbox(
            file_list_container,
            yscrollcommand=scrollbar.set,
            height=5,
            font=('微软雅黑', 9),
            selectmode=tk.EXTENDED
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        # 按钮区域
        button_frame = ttk.Frame(file_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(button_frame, text="添加文件", command=self.add_files).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="删除选中", command=self.remove_selected_files).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="清空列表", command=self.clear_file_list).pack(side=tk.LEFT)

        # 处理选项区域
        options_frame = ttk.LabelFrame(main_frame, text="处理选项", padding="15")
        options_frame.pack(fill=tk.X, pady=(0, 15))

        # 输出选项
        self.add_wildcard_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="自动添加通配符*（无*的根域名自动加上*）",
            variable=self.add_wildcard_var
        ).pack(anchor=tk.W)

        # 输出目录选择
        output_frame = ttk.Frame(options_frame)
        output_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(output_frame, text="输出目录:").pack(side=tk.LEFT)

        self.output_dir_var = tk.StringVar()
        self.output_dir_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var, width=50)
        self.output_dir_entry.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)

        ttk.Button(output_frame, text="浏览...", command=self.select_output_dir).pack(side=tk.LEFT)

        # 处理按钮
        process_button_frame = ttk.Frame(main_frame)
        process_button_frame.pack(pady=(0, 15))

        self.process_button = ttk.Button(
            process_button_frame,
            text="开始处理",
            command=self.start_processing,
            width=20
        )
        self.process_button.pack()

        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 15))

        # 日志输出区域
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            font=('Consolas', 10),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 状态栏
        self.status_label = ttk.Label(main_frame, text="就绪", style='Status.TLabel')
        self.status_label.pack(pady=(5, 0))

    def log_message(self, message):
        """在日志区域添加消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def update_status(self, message):
        """更新状态栏"""
        self.status_label.config(text=message)
        self.root.update()

    def add_files(self):
        """添加文件到列表"""
        files = filedialog.askopenfilenames(
            title="选择域名文件",
            filetypes=[
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )

        for file_path in files:
            if file_path not in self.files_to_process:
                self.files_to_process.append(file_path)
                filename = os.path.basename(file_path)
                self.file_listbox.insert(tk.END, filename)

        if files:
            self.log_message(f"添加了 {len(files)} 个文件")

    def remove_selected_files(self):
        """删除选中的文件"""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("警告", "请先选择要删除的文件")
            return

        # 从后往前删除，避免索引变化
        for index in reversed(selected_indices):
            self.file_listbox.delete(index)
            del self.files_to_process[index]

        self.log_message(f"删除了 {len(selected_indices)} 个文件")

    def clear_file_list(self):
        """清空文件列表"""
        if self.files_to_process:
            if messagebox.askyesno("确认", "确定要清空所有文件吗？"):
                self.file_listbox.delete(0, tk.END)
                self.files_to_process.clear()
                self.log_message("已清空文件列表")
        else:
            messagebox.showinfo("提示", "文件列表已经是空的")

    def select_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir_var.set(directory)
            self.log_message(f"输出目录设置为: {directory}")

    def extract_root_domain(self, domain):
        """提取根域名（最后两部分）"""
        if not domain or not isinstance(domain, str):
            return None

        domain = domain.strip().lower()

        # 如果是IP地址，直接返回（IP地址不加*）
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$'
        if re.match(ip_pattern, domain):
            return domain.split(':')[0]

        # 移除协议头
        if '://' in domain:
            domain = domain.split('://')[1]

        # 移除端口、路径、查询参数
        domain = domain.split(':')[0].split('/')[0].split('?')[0]

        # 分割域名
        parts = domain.split('.')

        if len(parts) < 2:
            return domain

        # 处理特殊TLD（如.co.uk, .com.cn）
        special_tlds = {'co', 'com', 'net', 'org', 'edu', 'gov', 'ac'}
        country_tlds = {'uk', 'jp', 'cn', 'au', 'tw', 'hk', 'kr', 'us'}

        if len(parts) >= 3:
            tld = parts[-1]
            second_last = parts[-2]
            if tld in country_tlds and second_last in special_tlds:
                return '.'.join(parts[-2:])

        # 返回最后两部分
        return '.'.join(parts[-2:])

    def process_files(self):
        """处理文件的主函数"""
        try:
            self.is_processing = True
            self.process_button.config(state='disabled')
            self.progress.start()

            # 清空之前的日志
            self.log_text.delete(1.0, tk.END)
            self.all_root_domains.clear()

            # 检查文件列表
            if not self.files_to_process:
                messagebox.showwarning("警告", "请先添加要处理的文件")
                return

            # 检查输出目录
            output_dir = self.output_dir_var.get()
            if not output_dir:
                output_dir = os.path.dirname(self.files_to_process[0])
                self.output_dir_var.set(output_dir)
                self.log_message(f"未指定输出目录，使用文件所在目录: {output_dir}")

            # 创建输出目录（如果不存在）
            os.makedirs(output_dir, exist_ok=True)

            self.log_message("开始处理文件...")
            self.update_status("正在处理文件...")

            # 统计信息
            file_stats = []
            total_lines_all = 0
            valid_domains_all = 0

            # 处理每个文件
            for i, file_path in enumerate(self.files_to_process, 1):
                filename = os.path.basename(file_path)
                self.log_message(f"\n处理文件 [{i}/{len(self.files_to_process)}]: {filename}")
                self.update_status(f"正在处理: {filename}")

                if not os.path.exists(file_path):
                    self.log_message(f"  ❌ 文件不存在")
                    continue

                file_root_domains = set()
                file_total_lines = 0
                file_valid_domains = 0

                # 尝试不同编码读取
                encodings = ['utf-8', 'gbk', 'latin-1']
                success = False

                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            for line in f:
                                file_total_lines += 1
                                line = line.strip()
                                if not line or line.startswith('#') or line.startswith('//'):
                                    continue

                                # 提取域名（取第一个字段）
                                parts = line.split()
                                if parts:
                                    domain = parts[0]
                                    root = self.extract_root_domain(domain)
                                    if root:
                                        file_root_domains.add(root)
                                        self.all_root_domains.add(root)
                                        file_valid_domains += 1

                        success = True
                        self.log_message(f"  ✅ 成功读取，编码: {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        self.log_message(f"  ❌ 读取失败: {e}")
                        continue

                if not success:
                    self.log_message(f"  ❌ 无法读取文件 {filename}")
                    continue

                # 记录文件统计信息
                file_stats.append({
                    'filename': filename,
                    'total_lines': file_total_lines,
                    'valid_domains': file_valid_domains,
                    'unique_roots': len(file_root_domains)
                })

                total_lines_all += file_total_lines
                valid_domains_all += file_valid_domains

                self.log_message(f"  📊 文件行数: {file_total_lines}")
                self.log_message(f"  📊 有效域名: {file_valid_domains}")
                self.log_message(f"  📊 唯一根域名: {len(file_root_domains)}")

            # 检查是否成功处理了文件
            if not file_stats:
                self.log_message("\n❌ 没有成功处理任何文件")
                self.update_status("处理失败")
                return

            # 输出总体统计信息
            self.log_message("\n" + "=" * 50)
            self.log_message("📈 总体统计信息")
            self.log_message("=" * 50)
            self.log_message(f"处理文件数: {len(file_stats)}")

            for stat in file_stats:
                self.log_message(f"\n📄 {stat['filename']}:")
                self.log_message(f"  文件行数: {stat['total_lines']}")
                self.log_message(f"  有效域名: {stat['valid_domains']}")
                self.log_message(f"  唯一根域名: {stat['unique_roots']}")

            self.log_message(f"\n📊 总计:")
            self.log_message(f"  总行数: {total_lines_all}")
            self.log_message(f"  总有效域名: {valid_domains_all}")
            self.log_message(f"  合并后的唯一根域名总数: {len(self.all_root_domains)}")

            # 处理结果
            if self.add_wildcard_var.get():
                # 有*的保留，没有*的加上*
                final_results = []
                for root in sorted(self.all_root_domains):
                    if root.startswith('*'):
                        final_results.append(root)
                    else:
                        final_results.append(f"*{root}")

                output_filename = "wildcard_root_domains.txt"
                self.log_message(f"\n✅ 已自动添加通配符*")
            else:
                # 保持原样
                final_results = sorted(self.all_root_domains)
                output_filename = "original_root_domains.txt"
                self.log_message(f"\n✅ 保持原始格式（不添加*）")

            # 保存处理后的结果
            output_file = os.path.join(output_dir, output_filename)
            with open(output_file, 'w', encoding='utf-8') as f:
                for root in final_results:
                    f.write(f"{root}\n")

            self.log_message(f"\n💾 结果已保存到: {output_file}")
            self.log_message(f"\n📋 处理后的根域名列表（前20个示例）:")
            for i, root in enumerate(final_results[:20], 1):
                self.log_message(f"  {i:2d}. {root}")

            if len(final_results) > 20:
                self.log_message(f"  ... 还有 {len(final_results) - 20} 个根域名")

            # 显示处理完成提示
            self.log_message("\n" + "=" * 50)
            self.log_message("🎉 处理完成！")
            self.update_status(f"处理完成，共提取 {len(self.all_root_domains)} 个唯一根域名")

            # 询问是否打开输出目录
            if messagebox.askyesno("处理完成",
                                   f"处理完成！\n共提取 {len(self.all_root_domains)} 个唯一根域名\n\n是否打开输出目录？"):
                os.startfile(output_dir)

        except Exception as e:
            self.log_message(f"\n❌ 处理过程中出现错误: {str(e)}")
            self.update_status("处理出错")
            messagebox.showerror("错误", f"处理过程中出现错误:\n{str(e)}")

        finally:
            self.is_processing = False
            self.process_button.config(state='normal')
            self.progress.stop()

    def start_processing(self):
        """开始处理文件（在新线程中）"""
        if self.is_processing:
            return

        if not self.files_to_process:
            messagebox.showwarning("警告", "请先添加要处理的文件")
            return

        # 在新线程中处理文件，避免界面卡死
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()


def main():
    root = tk.Tk()
    app = DomainExtractorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()