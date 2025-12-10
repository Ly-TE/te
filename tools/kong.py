import tkinter as tk
from tkinter import ttk


def process_text():
    input_text = input_text_widget.get(1.0, tk.END).strip()
    operation_value = operation.get()
    if operation_value == "去除空格":
        processed_text = input_text.replace(" ", "")
    elif operation_value == "转换为大写":
        processed_text = input_text.upper()
    elif operation_value == "转换为小写":
        processed_text = input_text.lower()
    else:
        processed_text = input_text
    output_text_widget.delete(1.0, tk.END)
    output_text_widget.insert(tk.END, processed_text)


# 创建主窗口
root = tk.Tk()
root.title("文本处理程序")
root.geometry("1500x1200")  # 设置窗口大小
root.configure(bg='#f0f0f0')  # 设置窗口背景颜色


# 创建并放置输入文本框
input_text_widget = tk.Text(root, height=15, width=60, bg='#ffffff', fg='#333333',
                        font=('Arial', 12), borderwidth=2, relief=tk.SOLID)  # 增大输入文本框的高度和宽度
input_text_widget.grid(row=0, column=0, rowspan=2, padx=(20, 10), pady=20, sticky="nsew")


# 创建并放置操作选项
operation = tk.StringVar()
operation.set("去除空格")


operation_menu = ttk.Combobox(root, textvariable=operation, values=["去除空格", "转换为大写", "转换为小写"], font=('Arial', 12))
operation_menu.grid(row=0, column=1, padx=(0, 20), pady=(20, 0), sticky="n")


# 创建并放置处理按钮
button = ttk.Button(root, text="处理文本", command=process_text, style='TButton')
button.grid(row=1, column=1, padx=(0, 20), pady=(0, 20), sticky="n")


# 创建并放置输出文本框
output_text_widget = tk.Text(root, height=15, width=60, bg='#ffffff', fg='#333333',
                         font=('Arial', 12), borderwidth=2, relief=tk.SOLID)  # 增大输出文本框的高度和宽度
output_text_widget.grid(row=0, column=2, rowspan=2, padx=(10, 20), pady=20, sticky="nsew")


# 配置网格布局权重
root.columnconfigure(0, weight=1)
root.columnconfigure(2, weight=1)
root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=1)


# 创建样式
style = ttk.Style()
style.configure('TButton', font=('Arial', 12), padding=10, background='#4CAF50', foreground='white')
style.map('TButton', background=[('active', '#45a049')])


# 运行主循环
root.mainloop()