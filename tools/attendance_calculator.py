import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import pandas as pd
import numpy as np


class AttendanceCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("考勤工时计算器")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # 设置中文字体
        self.style = ttk.Style()
        try:
            self.style.configure("TLabel", font=("微软雅黑", 10))
            self.style.configure("TButton", font=("微软雅黑", 10))
            self.style.configure("TEntry", font=("微软雅黑", 10))
            self.style.configure("Header.TLabel", font=("微软雅黑", 12, "bold"))
        except:
            pass  # 如果字体不存在，使用默认字体

        # 变量初始化
        self.file_path = tk.StringVar()
        self.manual_days = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        # 标题
        header = ttk.Label(self.root, text="考勤工时计算器", style="Header.TLabel")
        header.pack(pady=15)

        # 文件选择区域
        file_frame = ttk.Frame(self.root)
        file_frame.pack(fill=tk.X, padx=30, pady=5)

        ttk.Label(file_frame, text="Excel文件:").pack(side=tk.LEFT, padx=5)

        file_entry = ttk.Entry(file_frame, textvariable=self.file_path, width=40)
        file_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        browse_btn = ttk.Button(file_frame, text="浏览", command=self.browse_file)
        browse_btn.pack(side=tk.LEFT, padx=5)

        # 统计天数设置
        days_frame = ttk.Frame(self.root)
        days_frame.pack(fill=tk.X, padx=30, pady=10)

        ttk.Label(days_frame, text="统计有效天数:").pack(side=tk.LEFT, padx=5)

        days_entry = ttk.Entry(days_frame, textvariable=self.manual_days, width=10)
        days_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(days_frame, text="(留空则使用实际有效天数)").pack(side=tk.LEFT, padx=5)

        # 午休时间说明
        lunch_frame = ttk.Frame(self.root)
        lunch_frame.pack(fill=tk.X, padx=30, pady=5)

        ttk.Label(lunch_frame, text="午休扣除设置: 固定每天扣除1.5小时").pack(side=tk.LEFT, padx=5)

        # 计算按钮
        calc_btn = ttk.Button(self.root, text="开始计算", command=self.start_calculation, width=15)
        calc_btn.pack(pady=20)

        # 结果显示区域
        result_frame = ttk.LabelFrame(self.root, text="计算结果")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        self.result_display = tk.Text(result_frame, wrap=tk.WORD, font=("微软雅黑", 10))
        self.result_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.result_display.config(state=tk.DISABLED)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def browse_file(self):
        """打开文件选择对话框"""
        filetypes = (('Excel files', '*.xlsx'), ('All files', '*.*'))
        filename = filedialog.askopenfilename(title='选择Excel文件', initialdir='/', filetypes=filetypes)
        if filename:
            self.file_path.set(filename)
            self.status_var.set(f"已选择文件: {Path(filename).name}")

    def start_calculation(self):
        """开始计算"""
        file_path = self.file_path.get().strip()
        if not file_path:
            messagebox.showerror("错误", "请先选择Excel文件")
            return

        if not Path(file_path).exists():
            messagebox.showerror("错误", f"文件不存在: {file_path}")
            return

        # 处理统计天数
        manual_days = None
        days_input = self.manual_days.get().strip()
        if days_input:
            try:
                manual_days = int(days_input)
                if manual_days <= 0:
                    messagebox.showerror("错误", "统计天数必须大于0")
                    return
            except ValueError:
                messagebox.showerror("错误", "统计天数必须是有效的整数")
                return

        # 清空之前的结果
        self.result_display.config(state=tk.NORMAL)
        self.result_display.delete(1.0, tk.END)
        self.result_display.config(state=tk.DISABLED)

        # 在新线程中执行计算
        self.status_var.set("正在计算...")
        threading.Thread(target=self.perform_calculation, args=(file_path, manual_days), daemon=True).start()

    def perform_calculation(self, file_path, manual_days):
        """执行实际计算逻辑"""
        try:
            result = self.calculate_average_work_hours(file_path, lunch_hours=1.5, manual_days=manual_days)
            self.root.after(0, self.display_result, result)
            self.root.after(0, lambda: self.status_var.set("计算完成"))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.show_error_message(msg))
            self.root.after(0, lambda: self.status_var.set("计算出错"))

    def show_error_message(self, message):
        """显示错误消息"""
        messagebox.showerror("处理错误", message)

    def display_result(self, result):
        """显示计算结果"""
        if not result:
            self.result_display.config(state=tk.NORMAL)
            self.result_display.insert(tk.END, "没有计算结果可显示")
            self.result_display.config(state=tk.DISABLED)
            return

        self.result_display.config(state=tk.NORMAL)
        self.result_display.insert(tk.END, "=== 计算结果 ===\n\n")
        self.result_display.insert(tk.END, f"总计时长: {result['总计时长(小时)']} 小时\n")
        self.result_display.insert(tk.END, f"数据中实际有效天数: {result['实际打卡天数']} 天\n")
        self.result_display.insert(tk.END, f"工作日: {result['统计天数']} 天\n")
        self.result_display.insert(tk.END, f"每天扣除午休时长: {result['午休扣除时长(小时)']} 小时\n")
        self.result_display.insert(tk.END,
                                   f"扣除午休后的平均工作时长: {result['扣除午休后的平均工作时长(小时)']} 小时/月\n")
        self.result_display.config(state=tk.DISABLED)

    def calculate_average_work_hours(self, file_path, lunch_hours=1.5, manual_days=None):
        """计算实际工作时长"""
        try:
            # 尝试多种方式读取Excel
            df = None
            try:
                # 方法1：尝试多级表头
                df = pd.read_excel(file_path, sheet_name='概况统计与打卡明细', header=[2, 3])
                # 合并多级表头
                df.columns = ['_'.join(filter(pd.notna, col)).strip() if isinstance(col, tuple) else str(col)
                              for col in df.columns]
            except:
                # 方法2：备用方法
                df_raw = pd.read_excel(file_path, sheet_name='概况统计与打卡明细', header=None)
                header1 = df_raw.iloc[2].fillna('')
                header2 = df_raw.iloc[3].fillna('')

                combined_columns = []
                for i in range(len(header1)):
                    h1 = str(header1[i]).strip()
                    h2 = str(header2[i]).strip()
                    if h1 and h2 and h1 != h2:
                        combined = f"{h1}_{h2}"
                    elif h1:
                        combined = h1
                    elif h2:
                        combined = h2
                    else:
                        combined = f"列{i}"
                    combined_columns.append(combined)

                df = df_raw.iloc[4:].reset_index(drop=True)
                df.columns = combined_columns

            # 查找实际工作时长列
            work_hours_column = None
            for col in df.columns:
                if '实际工作时长' in str(col):
                    work_hours_column = col
                    break

            if not work_hours_column:
                raise ValueError("未找到'实际工作时长'列")

            # 转换数据
            def convert_value(val):
                if pd.isna(val):
                    return np.nan
                if isinstance(val, str):
                    val = val.strip()
                    if val in ('--', '', 'nan', 'NaN'):
                        return np.nan
                    try:
                        return float(val)
                    except:
                        return np.nan
                elif isinstance(val, (int, float)):
                    return float(val)
                return np.nan

            # 提取并处理数据
            converted_values = df[work_hours_column].apply(convert_value)
            work_hours = converted_values.dropna()

            if work_hours.empty:
                return None

            # 计算统计信息
            total_hours = work_hours.sum()
            original_average = total_hours / len(work_hours)

            # 确定统计天数
            if manual_days and manual_days > 0:
                stat_days = manual_days
                average_hours = total_hours / stat_days
            else:
                stat_days = len(work_hours)
                average_hours = original_average

            # 扣除午休时间
            adjusted_hours = average_hours - lunch_hours

            # 结果保留两位小数
            total_hours = round(total_hours, 2)
            average_hours = round(average_hours, 2)
            adjusted_hours = round(adjusted_hours, 2)
            original_average = round(original_average, 2)

            return {
                '总计时长(小时)': total_hours,
                '原始平均工作时长(小时)': original_average,
                '基于统计天数的平均工作时长(小时)': average_hours,
                '扣除午休后的平均工作时长(小时)': adjusted_hours,
                '统计天数': stat_days,
                '实际打卡天数': len(work_hours),
                '午休扣除时长(小时)': lunch_hours
            }

        except Exception as e:
            raise e


if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceCalculator(root)
    root.mainloop()