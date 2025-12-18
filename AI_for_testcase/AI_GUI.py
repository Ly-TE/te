import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
import json
import re
import threading
import os
import time
import copy


class APITestCaseGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("API测试用例生成器 - 增强版")
        self.root.geometry("1400x900")

        # 存储接口信息
        self.api_info = {
            'url': '',
            'method': 'POST',
            'headers': {},
            'params': {},
            'data': {},
            'files': {},
            'payload': {}
        }

        # 存储测试用例
        self.test_cases = []

        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # ==================== 左侧：接口输入区域 ====================
        input_frame = ttk.LabelFrame(main_frame, text="接口信息输入", padding="15")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # 输入格式选择
        format_frame = ttk.Frame(input_frame)
        format_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(format_frame, text="输入格式:").pack(side=tk.LEFT, padx=(0, 10))
        self.input_format = tk.StringVar(value="python")

        ttk.Radiobutton(format_frame, text="Python代码", variable=self.input_format,
                        value="python", command=self.on_format_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="cURL命令", variable=self.input_format,
                        value="curl", command=self.on_format_change).pack(side=tk.LEFT, padx=5)

        # 输入文本框
        self.input_text = scrolledtext.ScrolledText(input_frame, width=60, height=25,
                                                    font=('Consolas', 10))
        self.input_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 示例按钮
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        ttk.Button(button_frame, text="加载Python示例",
                   command=self.load_python_example).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="加载cURL示例",
                   command=self.load_curl_example).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="解析接口信息",
                   command=self.parse_interface).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="清空",
                   command=self.clear_input).pack(side=tk.LEFT, padx=2)

        # ==================== 中间：测试用例配置区域 ====================
        config_frame = ttk.LabelFrame(main_frame, text="测试用例配置", padding="15")
        config_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        config_frame.columnconfigure(0, weight=1)

        # 主测试类型选择
        main_type_frame = ttk.LabelFrame(config_frame, text="主测试类型", padding="10")
        main_type_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # 主测试类型按钮组
        button_group = ttk.Frame(main_type_frame)
        button_group.grid(row=0, column=0, sticky=tk.W)

        ttk.Button(button_group, text="全选",
                   command=lambda: self.select_all_main_types(True)).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_group, text="反选",
                   command=lambda: self.select_all_main_types(False)).pack(side=tk.LEFT, padx=2)

        # 主测试类型复选框
        self.main_type_vars = {}
        self.main_type_checkbuttons = {}
        main_types = ["正向", "负向", "边界值", "安全性"]

        checkbox_frame = ttk.Frame(main_type_frame)
        checkbox_frame.grid(row=1, column=0, sticky=tk.W, pady=(10, 0))

        for i, mtype in enumerate(main_types):
            var = tk.BooleanVar(value=True)
            self.main_type_vars[mtype] = var
            cb = ttk.Checkbutton(checkbox_frame, text=mtype, variable=var,
                                 command=lambda mt=mtype: self.on_main_type_change(mt))
            cb.grid(row=0, column=i, padx=10, pady=2, sticky=tk.W)
            self.main_type_checkbuttons[mtype] = cb

        # 测试子类型选择
        sub_type_frame = ttk.LabelFrame(config_frame, text="测试子类型选择", padding="10")
        sub_type_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        sub_type_frame.columnconfigure(0, weight=1)
        sub_type_frame.rowconfigure(0, weight=1)

        # 创建带滚动条的canvas用于子类型
        canvas = tk.Canvas(sub_type_frame, height=180, highlightthickness=0)
        scrollbar = ttk.Scrollbar(sub_type_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 子类型定义
        self.sub_type_groups = {
            "正向": ["仅传必要字段", "语义合法", "覆盖枚举组合", "其他正向"],
            "负向": ["无效值", "缺失必填字段", "格式错误", "类型错误", "语义非法", "其他负向"],
            "边界值": ["极大值/极小值", "超出最大/最小边界值", "Null/零值/空值", "字符串过长/过短"],
            "安全性": ["鉴权控制", "SQL注入", "模糊输入", "XSS注入", "命令行注入", "JSON注入", "NoSQL注入"]
        }

        # 创建子类型复选框
        self.sub_type_vars = {}
        self.sub_type_checkbuttons = {}
        row = 0
        col = 0

        for main_type, sub_types in self.sub_type_groups.items():
            type_group_frame = ttk.Frame(scrollable_frame, padding="5")
            type_group_frame.grid(row=row, column=col, sticky=tk.W, padx=5, pady=5)

            # 添加主类型标签
            ttk.Label(type_group_frame, text=main_type, font=('微软雅黑', 9, 'bold')).grid(row=0, column=0, sticky=tk.W,
                                                                                           pady=(0, 5))

            for idx, sub_type in enumerate(sub_types):
                var = tk.BooleanVar(value=True if main_type == "正向" else False)  # 正向默认选中
                key = f"{main_type}_{sub_type}"
                self.sub_type_vars[key] = var

                cb = ttk.Checkbutton(type_group_frame, text=sub_type, variable=var)
                cb.grid(row=idx + 1, column=0, sticky=tk.W, padx=2, pady=1)
                self.sub_type_checkbuttons[key] = cb

            col += 1
            if col > 2:
                col = 0
                row += 1

        # 子类型按钮组
        sub_type_buttons = ttk.Frame(scrollable_frame)
        sub_type_buttons.grid(row=row + 1, column=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        ttk.Button(sub_type_buttons, text="全选",
                   command=self.select_all_sub_types).pack(side=tk.LEFT, padx=2)
        ttk.Button(sub_type_buttons, text="反选",
                   command=self.toggle_sub_types).pack(side=tk.LEFT, padx=2)
        ttk.Button(sub_type_buttons, text="重置",
                   command=self.reset_sub_types).pack(side=tk.LEFT, padx=2)

        # 布局canvas和scrollbar
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 输出格式选择
        output_frame = ttk.LabelFrame(config_frame, text="输出格式选择", padding="10")
        output_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        self.output_format = tk.StringVar(value="python")
        ttk.Radiobutton(output_frame, text="Python代码", variable=self.output_format,
                        value="python").pack(side=tk.LEFT, padx=20)
        ttk.Radiobutton(output_frame, text="cURL命令", variable=self.output_format,
                        value="curl").pack(side=tk.LEFT, padx=20)

        # 生成按钮
        ttk.Button(config_frame, text="生成测试用例", command=self.generate_test_cases).grid(row=3, column=0,
                                                                                             pady=(10, 0))

        # 配置canvas网格
        sub_type_frame.columnconfigure(0, weight=1)
        sub_type_frame.rowconfigure(0, weight=1)

        # ==================== 右侧：结果显示区域 ====================
        result_frame = ttk.LabelFrame(main_frame, text="生成的测试用例", padding="15")
        result_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置结果区域的网格
        main_frame.columnconfigure(2, weight=3)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(1, weight=1)

        # 结果标题和按钮
        result_header = ttk.Frame(result_frame)
        result_header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        self.case_count_label = ttk.Label(result_header, text="已生成测试用例: 0",
                                          font=('微软雅黑', 10, 'bold'))
        self.case_count_label.pack(side=tk.LEFT)

        button_frame = ttk.Frame(result_header)
        button_frame.pack(side=tk.RIGHT)

        ttk.Button(button_frame, text="保存Python",
                   command=lambda: self.save_to_file("python")).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="保存cURL",
                   command=lambda: self.save_to_file("curl")).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="复制到剪贴板",
                   command=self.copy_to_clipboard).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="清空结果",
                   command=self.clear_results).pack(side=tk.LEFT, padx=2)

        # 结果显示文本框
        self.result_text = scrolledtext.ScrolledText(result_frame, width=70, height=30,
                                                     font=('Consolas', 9), wrap=tk.WORD)
        self.result_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 状态栏
        self.status_bar = ttk.Label(result_frame, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        # 配置网格权重
        input_frame.rowconfigure(1, weight=1)
        input_frame.columnconfigure(0, weight=1)
        input_frame.columnconfigure(1, weight=1)
        config_frame.rowconfigure(1, weight=1)
        config_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(1, weight=1)
        result_frame.columnconfigure(0, weight=1)

        # 初始选中正向相关子类型
        self.on_main_type_change("正向")

    def on_main_type_change(self, main_type):
        """主类型选择变化事件"""
        if self.main_type_vars[main_type].get():
            # 选中主类型时，选中所有相关子类型
            for sub_type in self.sub_type_groups[main_type]:
                key = f"{main_type}_{sub_type}"
                self.sub_type_vars[key].set(True)
        else:
            # 取消主类型时，取消所有相关子类型
            for sub_type in self.sub_type_groups[main_type]:
                key = f"{main_type}_{sub_type}"
                self.sub_type_vars[key].set(False)

    def select_all_main_types(self, select):
        """选择/取消所有主类型"""
        for mtype, var in self.main_type_vars.items():
            var.set(select)
            # 触发主类型变化事件
            self.on_main_type_change(mtype)

    def select_all_sub_types(self):
        """选择所有子类型"""
        for var in self.sub_type_vars.values():
            var.set(True)

    def toggle_sub_types(self):
        """反选子类型"""
        for var in self.sub_type_vars.values():
            var.set(not var.get())

    def reset_sub_types(self):
        """重置子类型选择"""
        for var in self.sub_type_vars.values():
            var.set(False)

    def on_format_change(self):
        """输入格式变更事件"""
        format_type = self.input_format.get()
        if format_type == "python":
            self.load_python_example()
        else:
            self.load_curl_example()

    def load_python_example(self):
        """加载Python示例"""
        example_code = '''import requests

url = "https://vf-thorfastapi.leigod.com/client/login/code?client_version=2.0.2.4&country_code=86&device_info=device_info&hardware_id=15ae58b1-ab6b-4ad9-8429-7f29d8a99350&mobile_num=17764000760&os_type=0&smscode=8888&smscode_key=FV0qixVilXu33NyUYRNp54dWRnD8oFhhEf49JdgVXN9Us95NKDaB20o5unF8abTN&src_channel=guanwang&is_off_rc4=off&locale=en"

payload={}
files={}
headers = {}

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)'''

        self.input_text.delete(1.0, tk.END)
        self.input_text.insert(1.0, example_code)

    def load_curl_example(self):
        """加载cURL示例"""
        example_curl = '''curl -X POST \\
  'https://vf-thorfastapi.leigod.com/client/login/code?client_version=2.0.2.4&country_code=86&device_info=device_info&hardware_id=15ae58b1-ab6b-4ad9-8429-7f29d8a99350&mobile_num=17764000760&os_type=0&smscode=8888&smscode_key=FV0qixVilXu33NyUYRNp54dWRnD8oFhhEf49JdgVXN9Us95NKDaB20o5unF8abTN&src_channel=guanwang&is_off_rc4=off&locale=en' \\
  -H 'Content-Type: application/json' \\
  -d '{}' '''

        self.input_text.delete(1.0, tk.END)
        self.input_text.insert(1.0, example_curl)

    def clear_input(self):
        """清空输入框"""
        self.input_text.delete(1.0, tk.END)

    def parse_interface(self):
        """解析接口信息"""
        try:
            content = self.input_text.get(1.0, tk.END).strip()
            if not content:
                messagebox.showwarning("警告", "请输入接口代码或cURL命令！")
                return

            format_type = self.input_format.get()

            if format_type == "python":
                self.parse_python_code(content)
            else:
                self.parse_curl_command(content)

            self.status_bar.config(text="接口信息解析成功！")

        except Exception as e:
            messagebox.showerror("解析错误", f"解析接口信息时出错：{str(e)}")
            self.status_bar.config(text="解析失败")

    def parse_python_code(self, code):
        """解析Python代码"""
        # 解析URL
        url_pattern = r'url\s*=\s*["\']([^"\']+)["\']'
        url_match = re.search(url_pattern, code)
        if url_match:
            url = url_match.group(1)
            self.api_info['url'] = url

            # 解析URL参数
            if '?' in url:
                base_url, query_string = url.split('?', 1)
                params = self.parse_query_string(query_string)
                self.api_info['params'] = params
                self.api_info['url'] = base_url

        # 解析请求方法
        method_pattern = r'requests\.request\(["\']([^"\']+)["\']'
        method_match = re.search(method_pattern, code)
        if method_match:
            self.api_info['method'] = method_match.group(1).upper()

        # 解析headers
        headers_pattern = r'headers\s*=\s*(\{[^}]+\})'
        headers_match = re.search(headers_pattern, code, re.DOTALL)
        if headers_match:
            try:
                headers_str = headers_match.group(1)
                headers_str = re.sub(r'#.*', '', headers_str)
                self.api_info['headers'] = eval(headers_str)
            except:
                pass

        # 解析payload/data
        payload_pattern = r'payload\s*=\s*(\{[^}]+\})'
        payload_match = re.search(payload_pattern, code, re.DOTALL)
        if payload_match:
            try:
                payload_str = payload_match.group(1)
                payload_str = re.sub(r'#.*', '', payload_str)
                self.api_info['payload'] = eval(payload_str)
            except:
                pass

    def parse_curl_command(self, curl_str):
        """解析cURL命令"""
        # 解析URL
        url_pattern = r"'(https?://[^']+)'"
        url_match = re.search(url_pattern, curl_str)
        if url_match:
            url = url_match.group(1)
            self.api_info['url'] = url

            # 解析URL参数
            if '?' in url:
                base_url, query_string = url.split('?', 1)
                params = self.parse_query_string(query_string)
                self.api_info['params'] = params
                self.api_info['url'] = base_url

        # 解析请求方法
        if '-X' in curl_str:
            method_pattern = r'-X\s+(\w+)'
            method_match = re.search(method_pattern, curl_str)
            if method_match:
                self.api_info['method'] = method_match.group(1).upper()
        else:
            self.api_info['method'] = 'GET' if 'curl' in curl_str else 'POST'

        # 解析headers
        headers = {}
        header_pattern = r"-H\s+['\"]([^:]+):\s*([^'\"]+)['\"]"
        header_matches = re.findall(header_pattern, curl_str)
        for key, value in header_matches:
            headers[key.strip()] = value.strip()
        self.api_info['headers'] = headers

        # 解析data
        data_pattern = r"-d\s+['\"]([^'\"]+)['\"]"
        data_match = re.search(data_pattern, curl_str)
        if data_match:
            try:
                data_str = data_match.group(1)
                if data_str.startswith('{') and data_str.endswith('}'):
                    self.api_info['payload'] = json.loads(data_str)
            except:
                pass

    def parse_query_string(self, query_string):
        """解析查询字符串"""
        params = {}
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key.strip()] = value.strip()
        return params

    def generate_test_cases(self):
        """生成测试用例"""
        try:
            # 获取选中的主测试类型
            selected_main_types = [mtype for mtype, var in self.main_type_vars.items() if var.get()]

            if not selected_main_types:
                messagebox.showwarning("警告", "请至少选择一个主测试类型！")
                return

            # 获取选中的子测试类型
            selected_sub_types = []
            for key, var in self.sub_type_vars.items():
                if var.get():
                    selected_sub_types.append(key)

            if not selected_sub_types:
                messagebox.showwarning("警告", "请至少选择一个子测试类型！")
                return

            # 检查接口信息
            if not self.api_info.get('url'):
                messagebox.showwarning("警告", "请先解析接口信息！")
                return

            # 清空之前的测试用例
            self.test_cases = []

            # 生成测试用例
            output_format = self.output_format.get()
            test_cases_text = ""

            if output_format == "python":
                test_cases_text = self.generate_python_test_cases(selected_main_types, selected_sub_types)
            else:
                test_cases_text = self.generate_curl_test_cases(selected_main_types, selected_sub_types)

            # 显示生成的测试用例
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, test_cases_text)

            # 更新状态
            count = len(self.test_cases)
            self.case_count_label.config(text=f"已生成测试用例: {count}")
            self.status_bar.config(text=f"已生成 {count} 个测试用例 | 输出格式: {output_format}")

        except Exception as e:
            messagebox.showerror("错误", f"生成测试用例时出错：{str(e)}")
            self.status_bar.config(text="生成失败")

    def generate_python_test_cases(self, main_types, sub_types):
        """生成Python格式的测试用例"""
        base_url = self.api_info['url']
        method = self.api_info['method']
        base_headers = copy.deepcopy(self.api_info.get('headers', {}))
        base_params = copy.deepcopy(self.api_info.get('params', {}))
        base_payload = copy.deepcopy(self.api_info.get('payload', {}))

        result = f"""# API测试用例 - Python格式
# 接口地址: {base_url}
# 请求方法: {method}
# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
import requests
import json

class TestAPICases:
    \"\"\"API测试用例类\"\"\"

    BASE_URL = "{base_url}"
    BASE_HEADERS = {json.dumps(base_headers, indent=2, ensure_ascii=False)}

    def make_request(self, params=None, headers=None, data=None):
        \"\"\"发送请求\"\"\"
        try:
            # 合并参数
            request_headers = {{**self.BASE_HEADERS, **(headers or {{}})}}

            response = requests.request(
                method="{method}",
                url=self.BASE_URL,
                headers=request_headers,
                params=params,
                json=data,
                timeout=30
            )

            return response

        except Exception as e:
            print(f"请求异常: {{str(e)}}")
            return None
"""

        # 生成测试用例方法
        case_number = 1

        for main_type in main_types:
            for sub_type_key in sub_types:
                if sub_type_key.startswith(f"{main_type}_"):
                    sub_type = sub_type_key.split('_', 1)[1]

                    # 根据类型生成测试用例
                    if main_type == "正向":
                        cases = self.generate_positive_case_data(sub_type, base_params, base_payload)
                    elif main_type == "负向":
                        cases = self.generate_negative_case_data(sub_type, base_params, base_payload)
                    elif main_type == "边界值":
                        cases = self.generate_boundary_case_data(sub_type, base_params, base_payload)
                    elif main_type == "安全性":
                        cases = self.generate_security_case_data(sub_type, base_params, base_payload)
                    else:
                        cases = []

                    for case_data in cases:
                        method_name = f"test_{main_type}_{sub_type}_{case_number:03d}"
                        method_name = method_name.replace(' ', '_').replace('-', '_').lower()
                        case_desc = f"{main_type}-{sub_type}-{case_data['name']}"

                        # 生成参数
                        params_dict = {}
                        if 'params' in case_data:
                            params_dict = copy.deepcopy(case_data['params'])

                        headers_dict = {}
                        if 'headers' in case_data:
                            headers_dict = copy.deepcopy(case_data['headers'])

                        data_dict = {}
                        if 'data' in case_data:
                            data_dict = copy.deepcopy(case_data['data'])

                        result += f"""

    def {method_name}(self):
        \"\"\"{case_desc}\"\"\"
        params = {json.dumps(params_dict, indent=4, ensure_ascii=False)}
        headers = {json.dumps(headers_dict, indent=4, ensure_ascii=False)}
        data = {json.dumps(data_dict, indent=4, ensure_ascii=False)}

        print(f"\\n{'=' * 60}")
        print(f"执行测试用例: {case_desc}")
        print(f"请求参数: {{params}}")

        response = self.make_request(params=params, headers=headers, data=data)

        if response:
            print(f"状态码: {{response.status_code}}")
            print(f"响应内容: {{response.text[:200]}}")
            # 断言示例
            # assert response.status_code == 200
            # assert 'success' in response.text
        else:
            print("请求失败")
"""

                        # 保存测试用例数据
                        self.test_cases.append({
                            'type': f"{main_type}-{sub_type}",
                            'name': case_desc,
                            'method': method_name,
                            'params': params_dict,
                            'headers': headers_dict,
                            'data': data_dict
                        })

                        case_number += 1

        # 添加执行示例
        result += f"""

# 执行测试示例
if __name__ == "__main__":
    tester = TestAPICases()

    # 执行所有测试
    test_methods = [method for method in dir(tester) if method.startswith('test_')]

    print(f"开始执行 {{len(test_methods)}} 个测试用例...")
    for method_name in test_methods:
        method = getattr(tester, method_name)
        try:
            method()
        except Exception as e:
            print(f"测试 {{method_name}} 执行失败: {{str(e)}}")

    print("\\n所有测试用例执行完成！")
"""

        return result

    def generate_curl_test_cases(self, main_types, sub_types):
        """生成cURL格式的测试用例"""
        base_url = self.api_info['url']
        method = self.api_info['method']
        base_headers = copy.deepcopy(self.api_info.get('headers', {}))
        base_params = copy.deepcopy(self.api_info.get('params', {}))
        base_payload = copy.deepcopy(self.api_info.get('payload', {}))

        result = f"""# API测试用例 - cURL格式
# 接口地址: {base_url}
# 请求方法: {method}
# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

"""

        case_number = 1

        for main_type in main_types:
            for sub_type_key in sub_types:
                if sub_type_key.startswith(f"{main_type}_"):
                    sub_type = sub_type_key.split('_', 1)[1]

                    # 根据类型生成测试用例
                    if main_type == "正向":
                        cases = self.generate_positive_case_data(sub_type, base_params, base_payload)
                    elif main_type == "负向":
                        cases = self.generate_negative_case_data(sub_type, base_params, base_payload)
                    elif main_type == "边界值":
                        cases = self.generate_boundary_case_data(sub_type, base_params, base_payload)
                    elif main_type == "安全性":
                        cases = self.generate_security_case_data(sub_type, base_params, base_payload)
                    else:
                        cases = []

                    for case_data in cases:
                        case_desc = f"{main_type}-{sub_type}-{case_data['name']}"

                        # 构建参数
                        params_dict = copy.deepcopy(base_params)
                        if 'params' in case_data:
                            params_dict.update(case_data['params'])

                        headers_dict = copy.deepcopy(base_headers)
                        if 'headers' in case_data:
                            headers_dict.update(case_data['headers'])

                        data_dict = copy.deepcopy(base_payload)
                        if 'data' in case_data:
                            data_dict.update(case_data['data'])

                        # 构建cURL命令
                        curl_cmd = f"# 测试用例 {case_number}: {case_desc}\n"
                        curl_cmd += f"curl -X {method} \\\\\n"

                        # 构建URL参数
                        if params_dict:
                            param_str = '&'.join([f"{k}={v}" for k, v in params_dict.items()])
                            full_url = f"{base_url}?{param_str}"
                        else:
                            full_url = base_url

                        curl_cmd += f"  '{full_url}' \\\\\n"

                        # 添加headers
                        for key, value in headers_dict.items():
                            if value:  # 只添加有值的header
                                curl_cmd += f"  -H '{key}: {value}' \\\\\n"

                        # 添加data
                        if data_dict:
                            data_str = json.dumps(data_dict, ensure_ascii=False)
                            curl_cmd += f"  -d '{data_str}'"

                        # 移除最后的反斜杠
                        curl_cmd = curl_cmd.rstrip(' \\\\\n') + '\n'

                        result += curl_cmd + "\n"

                        # 保存测试用例数据
                        self.test_cases.append({
                            'type': f"{main_type}-{sub_type}",
                            'name': case_desc,
                            'curl': curl_cmd,
                            'params': params_dict,
                            'headers': headers_dict,
                            'data': data_dict
                        })

                        case_number += 1

        return result

    def generate_positive_case_data(self, sub_type, base_params, base_payload):
        """生成正向测试用例数据"""
        cases = []

        if sub_type == "仅传必要字段":
            # 假设必要字段
            required_fields = ['mobile_num', 'smscode', 'smscode_key', 'client_version']
            params = {}
            for field in required_fields:
                if field in base_params:
                    params[field] = base_params[field]
                else:
                    # 提供默认值
                    if field == 'mobile_num':
                        params[field] = '17764000760'
                    elif field == 'smscode':
                        params[field] = '8888'
                    elif field == 'smscode_key':
                        params[field] = 'test_key_123'
                    elif field == 'client_version':
                        params[field] = '2.0.2.4'

            cases.append({
                'name': '必要字段',
                'params': params
            })

        elif sub_type == "语义合法":
            cases.append({
                'name': '合法参数',
                'params': {
                    'client_version': '2.0.2.4',
                    'country_code': '86',
                    'mobile_num': '17764000761',
                    'os_type': '0',
                    'smscode': '123456',
                    'smscode_key': 'valid_key_1234567890',
                    'src_channel': 'guanwang'
                }
            })

        elif sub_type == "覆盖枚举组合":
            # 枚举测试
            enum_cases = [
                {'name': '组合1', 'params': {'os_type': '0', 'src_channel': 'guanwang'}},
                {'name': '组合2', 'params': {'os_type': '1', 'src_channel': 'appstore'}},
                {'name': '组合3', 'params': {'os_type': '0', 'src_channel': 'huawei'}},
            ]
            cases.extend(enum_cases)

        elif sub_type == "其他正向":
            cases.append({
                'name': '正常流程',
                'params': base_params.copy()
            })

        return cases

    def generate_negative_case_data(self, sub_type, base_params, base_payload):
        """生成负向测试用例数据"""
        cases = []

        if sub_type == "缺失必填字段":
            required_fields = ['mobile_num', 'smscode', 'smscode_key']
            for field in required_fields[:2]:
                params = base_params.copy()
                if field in params:
                    del params[field]
                    cases.append({
                        'name': f'缺失_{field}',
                        'params': params
                    })

        elif sub_type == "格式错误":
            cases.extend([
                {'name': '手机号格式错误', 'params': {'mobile_num': '12345'}},
                {'name': '验证码格式错误', 'params': {'smscode': 'abc'}},
                {'name': '版本号格式错误', 'params': {'client_version': 'v2.0'}},
            ])

        elif sub_type == "类型错误":
            cases.extend([
                {'name': '数值类型错误', 'params': {'country_code': 'abc'}},
                {'name': '布尔类型错误', 'params': {'is_off_rc4': 'yes'}},
            ])

        elif sub_type == "无效值":
            cases.extend([
                {'name': '无效国家代码', 'params': {'country_code': '999'}},
                {'name': '无效渠道', 'params': {'src_channel': 'unknown'}},
            ])

        elif sub_type == "语义非法":
            cases.append({
                'name': '过期验证码',
                'params': {'smscode': '000000', 'smscode_key': 'expired_key'}
            })

        elif sub_type == "其他负向":
            cases.append({
                'name': '频率限制',
                'params': {'mobile_num': '17764000760'}
            })

        return cases

    def generate_boundary_case_data(self, sub_type, base_params, base_payload):
        """生成边界值测试用例数据"""
        cases = []

        if sub_type == "字符串过长/过短":
            cases.extend([
                {'name': '超长手机号', 'params': {'mobile_num': '1' * 50}},
                {'name': '超短验证码', 'params': {'smscode': '1'}},
                {'name': '超长密钥', 'params': {'smscode_key': 'k' * 1000}},
            ])

        elif sub_type == "极大值/极小值":
            cases.extend([
                {'name': '最大版本号', 'params': {'client_version': '9.9.9.9'}},
                {'name': '最小版本号', 'params': {'client_version': '0.0.0.1'}},
            ])

        elif sub_type == "Null/零值/空值":
            cases.extend([
                {'name': '空手机号', 'params': {'mobile_num': ''}},
                {'name': '空验证码', 'params': {'smscode': ''}},
                {'name': 'null值', 'params': {'device_info': 'null'}},
            ])

        elif sub_type == "超出最大/最小边界值":
            cases.extend([
                {'name': '超大国家代码', 'params': {'country_code': '99999'}},
                {'name': '负值测试', 'params': {'os_type': '-1'}},
            ])

        return cases

    def generate_security_case_data(self, sub_type, base_params, base_payload):
        """生成安全性测试用例数据"""
        cases = []

        if sub_type == "SQL注入":
            sql_payloads = [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "' UNION SELECT * FROM users --",
            ]
            for i, payload in enumerate(sql_payloads):
                cases.append({
                    'name': f'SQL注入_{i + 1}',
                    'params': {'smscode_key': payload}
                })

        elif sub_type == "XSS注入":
            xss_payloads = [
                '<script>alert("xss")</script>',
                '<img src=x onerror=alert(1)>',
                '<svg/onload=alert(1)>',
            ]
            for i, payload in enumerate(xss_payloads):
                cases.append({
                    'name': f'XSS注入_{i + 1}',
                    'params': {'device_info': payload}
                })

        elif sub_type == "JSON注入":
            cases.append({
                'name': 'JSON注入',
                'data': {'malicious': 'test'}
            })

        elif sub_type == "鉴权控制":
            cases.append({
                'name': '无鉴权访问',
                'headers': {'Authorization': ''}
            })

        else:
            # 其他安全性测试类型
            cases.append({
                'name': f'{sub_type}测试',
                'params': {'test_param': 'test_value'}
            })

        return cases

    def get_required_fields(self):
        """获取必要字段"""
        return ['mobile_num', 'smscode', 'smscode_key', 'client_version']

    def save_to_file(self, file_type):
        """保存测试用例到文件"""
        if not self.test_cases:
            messagebox.showwarning("警告", "没有测试用例可保存！")
            return

        try:
            # 获取保存路径
            default_name = f"api_test_cases_{time.strftime('%Y%m%d_%H%M%S')}"
            if file_type == "python":
                filetypes = [("Python files", "*.py"), ("All files", "*.*")]
                filename = filedialog.asksaveasfilename(
                    defaultextension=".py",
                    filetypes=filetypes,
                    initialfile=f"{default_name}.py"
                )
            else:
                filetypes = [("Text files", "*.txt"), ("All files", "*.*")]
                filename = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=filetypes,
                    initialfile=f"{default_name}.txt"
                )

            if filename:
                # 获取要保存的内容
                content = self.result_text.get(1.0, tk.END)

                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)

                messagebox.showinfo("保存成功", f"测试用例已保存到:\n{filename}")
                self.status_bar.config(text=f"文件已保存: {os.path.basename(filename)}")

        except Exception as e:
            messagebox.showerror("保存失败", f"保存文件时出错：{str(e)}")

    def copy_to_clipboard(self):
        """复制到剪贴板"""
        try:
            content = self.result_text.get(1.0, tk.END)
            if content.strip():
                self.root.clipboard_clear()
                self.root.clipboard_append(content)
                self.status_bar.config(text="内容已复制到剪贴板")
            else:
                messagebox.showwarning("警告", "没有内容可复制！")
        except Exception as e:
            messagebox.showerror("复制失败", f"复制到剪贴板时出错：{str(e)}")

    def clear_results(self):
        """清空结果"""
        self.result_text.delete(1.0, tk.END)
        self.test_cases = []
        self.case_count_label.config(text="已生成测试用例: 0")
        self.status_bar.config(text="结果已清空")


def main():
    root = tk.Tk()
    app = APITestCaseGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    main()