from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import os
from pathlib import Path
import uuid

app = Flask(__name__)
CORS(app)  # 解决跨域问题

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制文件大小16MB


def calculate_attendance(file_path, manual_days=None):
    """计算考勤工时的核心函数"""
    try:
        # 读取Excel文件
        excel_file = pd.ExcelFile(file_path)

        # 检查工作表是否存在
        if '概况统计与打卡明细' not in excel_file.sheet_names:
            return {"error": "工作表“概况统计与打卡明细”不存在"}

        df = excel_file.parse('概况统计与打卡明细')

        # 设置列名
        df.columns = [
            '时间', '姓名', '账号', '基础信息_部门', '基础信息_职务',
            '考勤概况_所属规则', '考勤概况_班次', '考勤概况_最早', '考勤概况_最晚',
            '考勤概况_打卡次数(次)', '考勤概况_标准工作时长(小时)',
            '考勤概况_实际工作时长(小时)', '考勤概况_假勤申请', '考勤概况_考勤结果',
            '异常统计_异常合计(次)', '异常统计_迟到次数(次)', '异常统计_迟到时长(分钟)',
            '异常统计_早退次数(次)', '异常统计_早退时长(分钟)', '异常统计_旷工次数(次)',
            '异常统计_旷工时长(分钟)', '异常统计_缺卡次数(次)', '异常统计_地点异常(次)',
            '异常统计_设备异常(次)', '外出打卡_外出打卡次数(次)', '外出打卡_最早',
            '外出打卡_最晚', '加班统计_加班状态', '加班统计_加班时长(小时)',
            '加班统计_工作日加班计为调休(小时)', '加班统计_工作日加班计为加班费(小时)',
            '加班统计_休息日加班计为调休(小时)', '加班统计_休息日加班计为加班费(小时)',
            '加班统计_节假日加班计为调休(小时)', '加班统计_节假日加班计为加班费(小时)',
            '假勤统计_补卡次数(次)', '假勤统计_审批打卡次数(次)', '假勤统计_外勤次数(次)',
            '假勤统计_外出(小时)', '假勤统计_出差(天)', '假勤统计_年假(天)',
            '假勤统计_事假(天)', '假勤统计_病假(天)', '假勤统计_调休假(天)',
            '假勤统计_婚假(天)', '假勤统计_产假(天)', '假勤统计_陪产假(天)',
            '假勤统计_丧假(天)', '假勤统计_哺乳假(小时)', '假勤统计_产检假(天)',
            '假勤统计_护理假(天)', '假勤统计_育儿假(天)', '上班1_打卡时间',
            '上班1_打卡状态', '下班1_打卡时间', '下班1_打卡状态',
            '打卡时间记录', '打卡详情'
        ]

        # 从第4行开始加载数据
        df = df[3:]
        df = df.reset_index(drop=True)

        # 处理标准工作时长（核心：以此判断有效天数）
        standard_col = '考勤概况_标准工作时长(小时)'
        original_standard = df[standard_col].astype(str).str.strip()
        valid_mask = (
                (original_standard != '--') &
                (original_standard != '') &
                (~original_standard.isna())
        )
        valid_days = sum(valid_mask)

        # 处理实际工作时长
        actual_col = '考勤概况_实际工作时长(小时)'
        original_actual = df[actual_col].astype(str).str.strip()
        total_hours = 0.0
        details = []

        for i in range(len(original_standard)):
            record_num = i + 1
            std_val = original_standard[i]
            act_val = original_actual[i]

            if valid_mask[i]:
                status = "有效"
                try:
                    hour = float(act_val)
                    source = "实际工时"
                except:
                    hour = float(std_val)
                    source = "标准工时（实际工时无效）"
                total_hours += hour
            else:
                status = "无效（标准工时为空或--）"
                hour = 0.0
                source = "不计入"

            details.append({
                "record_num": record_num,
                "standard_hour": std_val,
                "actual_hour": act_val,
                "status": status,
                "used_hour": round(hour, 2),
                "source": source
            })

        # 确定统计天数
        if manual_days and manual_days > 0:
            stat_days = manual_days
        else:
            stat_days = valid_days

        if stat_days == 0:
            return {"error": "没有有效数据可计算"}

        # 计算平均值
        average_hours = total_hours / stat_days
        lunch_hours = 1.5  # 固定午休时间
        adjusted_hours = average_hours - lunch_hours

        return {
            "total_hours": round(total_hours, 2),
            "valid_days": valid_days,
            "stat_days": stat_days,
            "lunch_hours": lunch_hours,
            "average_hours": round(average_hours, 2),
            "adjusted_hours": round(adjusted_hours, 2),
            "total_records": len(original_standard),
            "invalid_records": len(original_standard) - valid_days,
            "details": details
        }

    except Exception as e:
        return {"error": f"计算失败：{str(e)}"}


@app.route('/')
def index():
    """返回前端页面"""
    return render_template('index.html')


@app.route('/api/calculate', methods=['POST'])
def calculate():
    """处理文件上传和计算请求"""
    # 检查文件是否上传
    if 'file' not in request.files:
        return jsonify({"error": "未上传文件"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400

    # 检查文件格式
    if not file.filename.endswith('.xlsx'):
        return jsonify({"error": "请上传Excel文件（.xlsx）"}), 400

    # 保存文件
    filename = f"{uuid.uuid4()}.xlsx"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # 获取手动输入的天数
    manual_days = None
    if 'manual_days' in request.form and request.form['manual_days'].strip():
        try:
            manual_days = int(request.form['manual_days'].strip())
            if manual_days <= 0:
                return jsonify({"error": "统计天数必须大于0"}), 400
        except ValueError:
            return jsonify({"error": "统计天数必须是整数"}), 400

    # 计算结果
    result = calculate_attendance(file_path, manual_days)

    # 删除临时文件
    os.remove(file_path)

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)