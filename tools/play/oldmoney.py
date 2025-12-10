import tkinter as tk
from tkinter import ttk, messagebox


class HubeiPensionCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("湖北省养老金计算器")
        self.root.geometry("650x620")
        self.root.resizable(True, True)

        # 设置字体确保中文正常显示
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("SimHei", 10))
        self.style.configure("TButton", font=("SimHei", 10))
        self.style.configure("TCombobox", font=("SimHei", 10))
        self.style.configure("Header.TLabel", font=("SimHei", 12, "bold"))

        # 主框架
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        ttk.Label(
            self.main_frame,
            text="湖北省养老金计算工具（嘉鱼县参考）",
            style="Header.TLabel"
        ).grid(row=0, column=0, columnspan=2, pady=10)

        # 选择保险类型
        ttk.Label(self.main_frame, text="养老保险类型:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.pension_type = tk.StringVar(value="灵活就业养老保险")
        pension_type_combo = ttk.Combobox(
            self.main_frame,
            textvariable=self.pension_type,
            values=["灵活就业养老保险", "城乡居民养老保险"],
            state="readonly",
            width=30
        )
        pension_type_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        pension_type_combo.bind("<<ComboboxSelected>>", self.update_fields)

        # 缴费信息框架
        self.payment_frame = ttk.LabelFrame(self.main_frame, text="基础缴费信息", padding="10")
        self.payment_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W + tk.E, pady=10)

        # 每年缴费金额
        ttk.Label(self.payment_frame, text="每年缴费金额（元）:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.annual_payment = tk.StringVar(value="9000")  # 可手动修改
        ttk.Entry(self.payment_frame, textvariable=self.annual_payment, width=20).grid(row=0, column=1, sticky=tk.W,
                                                                                       pady=5)

        # 缴费年限
        ttk.Label(self.payment_frame, text="缴费年限（年）:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.payment_years = tk.StringVar(value="15")  # 可手动修改
        ttk.Entry(self.payment_frame, textvariable=self.payment_years, width=20).grid(row=1, column=1, sticky=tk.W,
                                                                                      pady=5)

        # 灵活就业养老保险参数（默认嘉鱼县2024年数据）
        self.flexible_frame = ttk.LabelFrame(self.main_frame, text="灵活就业参数", padding="10")
        self.flexible_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W + tk.E, pady=10)

        ttk.Label(self.flexible_frame, text="上年度在岗职工月均工资（元）:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.average_salary = tk.StringVar(value="5969")  # 咸宁2024年数据，嘉鱼县参考
        ttk.Entry(self.flexible_frame, textvariable=self.average_salary, width=20).grid(row=0, column=1, sticky=tk.W,
                                                                                        pady=5)

        # 退休年龄（支持手动输入）
        ttk.Label(self.flexible_frame, text="退休年龄（岁，50-65）:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.retirement_age = tk.StringVar(value="60")  # 可手动修改
        self.retirement_entry = ttk.Entry(self.flexible_frame, textvariable=self.retirement_age, width=20)
        self.retirement_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        # 绑定退休年龄验证
        self.retirement_entry.bind("<FocusOut>", self.validate_retirement_age)

        # 城乡居民养老保险参数
        self.resident_frame = ttk.LabelFrame(self.main_frame, text="城乡居民参数", padding="10")
        self.resident_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W + tk.E, pady=10)
        self.resident_frame.grid_remove()  # 初始隐藏

        ttk.Label(self.resident_frame, text="基础养老金（元/月）:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.base_pension = tk.StringVar(value="180")  # 湖北地区参考值
        ttk.Entry(self.resident_frame, textvariable=self.base_pension, width=20).grid(row=0, column=1, sticky=tk.W,
                                                                                      pady=5)

        ttk.Label(self.resident_frame, text="政府补贴（元/年）:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.government_subsidy = tk.StringVar(value="60")  # 湖北地区参考值
        ttk.Entry(self.resident_frame, textvariable=self.government_subsidy, width=20).grid(row=1, column=1,
                                                                                            sticky=tk.W, pady=5)

        # 计算按钮
        ttk.Button(
            self.main_frame,
            text="计算养老金",
            command=self.calculate_pension
        ).grid(row=5, column=0, columnspan=2, pady=15)

        # 结果框架
        self.result_frame = ttk.LabelFrame(self.main_frame, text="计算结果", padding="10")
        self.result_frame.grid(row=6, column=0, columnspan=2, sticky=tk.W + tk.E + tk.N + tk.S, pady=10)

        # 结果显示
        self.result_text = tk.Text(self.result_frame, height=7, width=60, font=("SimHei", 10))
        self.result_text.grid(row=0, column=0, pady=5)
        self.result_text.config(state=tk.DISABLED)

        # 配置列权重，使其可以拉伸
        self.main_frame.columnconfigure(1, weight=1)
        self.payment_frame.columnconfigure(1, weight=1)
        self.flexible_frame.columnconfigure(1, weight=1)
        self.resident_frame.columnconfigure(1, weight=1)
        self.result_frame.columnconfigure(0, weight=1)
        self.result_frame.rowconfigure(0, weight=1)

    def update_fields(self, event):
        """根据选择的养老保险类型显示/隐藏相应的字段"""
        if self.pension_type.get() == "灵活就业养老保险":
            self.flexible_frame.grid()
            self.resident_frame.grid_remove()
        else:
            self.flexible_frame.grid_remove()
            self.resident_frame.grid()

    def validate_retirement_age(self, event):
        """验证退休年龄是否在合理范围内"""
        try:
            age = int(self.retirement_age.get())
            if not (50 <= age <= 65):
                messagebox.showwarning("年龄验证", "退休年龄应在50-65岁之间，请重新输入")
                self.retirement_age.set("60")  # 重置为默认值
        except ValueError:
            messagebox.showwarning("年龄验证", "请输入有效的数字作为退休年龄")
            self.retirement_age.set("60")  # 重置为默认值

    def get_payment_months(self, age):
        """根据退休年龄获取计发月数"""
        if age == 50:
            return 195
        elif age == 55:
            return 170
        elif age == 60:
            return 139
        elif age == 65:
            return 101
        else:
            # 对于中间年龄，使用线性插值估算
            # 参考数据：50岁195，55岁170，60岁139，65岁101
            if 50 < age < 55:
                return int(195 - (age - 50) * (195 - 170) / 5)
            elif 55 < age < 60:
                return int(170 - (age - 55) * (170 - 139) / 5)
            else:  # 60 < age < 65
                return int(139 - (age - 60) * (139 - 101) / 5)

    def calculate_pension(self):
        """计算养老金"""
        try:
            # 获取基本输入
            annual_payment = float(self.annual_payment.get())
            payment_years = int(self.payment_years.get())

            if payment_years < 15:
                messagebox.showwarning("警告", "缴费年限建议不低于15年，否则可能无法领取养老金")

            result = ""

            if self.pension_type.get() == "灵活就业养老保险":
                # 灵活就业养老保险计算
                average_salary = float(self.average_salary.get())
                retirement_age = int(self.retirement_age.get())

                # 验证退休年龄
                self.validate_retirement_age(None)
                retirement_age = int(self.retirement_age.get())  # 确保使用验证后的值

                # 计算缴费基数和平均缴费指数
                monthly_payment = annual_payment / 12  # 月缴费金额
                contribution_base = monthly_payment / 0.2  # 缴费基数 = 月缴费金额 / 20%
                avg_contribution_index = contribution_base / average_salary  # 平均缴费指数

                # 计算基础养老金
                basic_pension = (average_salary + average_salary * avg_contribution_index) / 2 * payment_years * 0.01

                # 获取计发月数
                monthly_payment_count = self.get_payment_months(retirement_age)

                # 计算个人账户养老金 (8%进入个人账户)
                personal_account = (annual_payment * 0.08 * 12 * payment_years) / monthly_payment_count

                # 总养老金
                total_pension = basic_pension + personal_account

                # 格式化结果
                result += f"灵活就业养老保险计算结果:\n"
                result += f"1. 基础养老金: {basic_pension:.2f} 元/月\n"
                result += f"2. 个人账户养老金: {personal_account:.2f} 元/月\n"
                result += f"3. 计发月数（基于{retirement_age}岁退休）: {monthly_payment_count}个月\n"
                result += f"4. 每月预计领取养老金总额: {total_pension:.2f} 元/月\n\n"
                result += f"注: 计算基于当前参数，实际金额可能因政策调整而变化"

            else:
                # 城乡居民养老保险计算
                base_pension = float(self.base_pension.get())
                government_subsidy = float(self.government_subsidy.get())

                # 计算个人账户养老金
                personal_account_total = (annual_payment + government_subsidy) * payment_years
                personal_account_pension = personal_account_total / 139  # 城乡居民固定139个月

                # 总养老金
                total_pension = base_pension + personal_account_pension

                # 格式化结果
                result += f"城乡居民养老保险计算结果:\n"
                result += f"1. 基础养老金: {base_pension:.2f} 元/月\n"
                result += f"2. 个人账户养老金: {personal_account_pension:.2f} 元/月\n"
                result += f"3. 每月预计领取养老金总额: {total_pension:.2f} 元/月\n\n"
                result += f"注: 城乡居民养老保险统一按60岁退休，计发月数为139个月"

            # 显示结果
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result)
            self.result_text.config(state=tk.DISABLED)

        except ValueError as e:
            messagebox.showerror("输入错误", f"请输入有效的数字: {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"计算过程中发生错误: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = HubeiPensionCalculator(root)
    root.mainloop()
