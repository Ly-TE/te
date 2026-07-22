"""
表单自动化示例
展示如何处理各种表单元素
"""
import pytest
import time
from playwright.sync_api import sync_playwright

from playwright_automation.core.page import BasePage
from playwright_automation.utils.logger import get_logger


# 示例HTML页面（用于测试）
TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>表单测试页面</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { padding: 8px; width: 300px; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        button:hover { background: #0056b3; }
        .error { color: red; font-size: 12px; }
        .success { color: green; font-size: 14px; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>用户注册表单</h1>
    <form id="registration-form">
        <div class="form-group">
            <label for="username">用户名 *</label>
            <input type="text" id="username" name="username" required>
            <span class="error" id="username-error"></span>
        </div>
        
        <div class="form-group">
            <label for="email">邮箱 *</label>
            <input type="email" id="email" name="email" required>
            <span class="error" id="email-error"></span>
        </div>
        
        <div class="form-group">
            <label for="password">密码 *</label>
            <input type="password" id="password" name="password" required>
            <span class="error" id="password-error"></span>
        </div>
        
        <div class="form-group">
            <label for="confirm-password">确认密码 *</label>
            <input type="password" id="confirm-password" name="confirm-password" required>
            <span class="error" id="confirm-password-error"></span>
        </div>
        
        <div class="form-group">
            <label for="gender">性别</label>
            <select id="gender" name="gender">
                <option value="">请选择</option>
                <option value="male">男</option>
                <option value="female">女</option>
                <option value="other">其他</option>
            </select>
        </div>
        
        <div class="form-group">
            <label>兴趣爱好</label>
            <input type="checkbox" id="hobby-reading" name="hobbies" value="reading"> 阅读
            <input type="checkbox" id="hobby-travel" name="hobbies" value="travel"> 旅行
            <input type="checkbox" id="hobby-sports" name="hobbies" value="sports"> 运动
        </div>
        
        <div class="form-group">
            <label for="bio">个人简介</label>
            <textarea id="bio" name="bio" rows="4"></textarea>
        </div>
        
        <div class="form-group">
            <input type="checkbox" id="terms" name="terms" required>
            <label for="terms" style="display:inline;">我已阅读并同意服务条款 *</label>
        </div>
        
        <button type="submit" id="submit-btn">注册</button>
        <button type="reset" id="reset-btn">重置</button>
    </form>
    
    <div id="success-message" class="success" style="display:none;">
        注册成功！
    </div>
    
    <script>
        document.getElementById('registration-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 简单验证
            var username = document.getElementById('username').value;
            var email = document.getElementById('email').value;
            var password = document.getElementById('password').value;
            var confirmPassword = document.getElementById('confirm-password').value;
            
            // 清空错误
            document.querySelectorAll('.error').forEach(el => el.textContent = '');
            
            // 验证
            if (!username) {
                document.getElementById('username-error').textContent = '用户名不能为空';
                return;
            }
            
            if (!email || !email.includes('@')) {
                document.getElementById('email-error').textContent = '请输入有效的邮箱';
                return;
            }
            
            if (password.length < 6) {
                document.getElementById('password-error').textContent = '密码至少6位';
                return;
            }
            
            if (password !== confirmPassword) {
                document.getElementById('confirm-password-error').textContent = '两次密码不一致';
                return;
            }
            
            // 显示成功
            document.getElementById('success-message').style.display = 'block';
        });
        
        document.getElementById('reset-btn').addEventListener('click', function() {
            document.getElementById('success-message').style.display = 'none';
            document.querySelectorAll('.error').forEach(el => el.textContent = '');
        });
    </script>
</body>
</html>
"""


# 测试1: 基础表单填写
def test_form_basic_fill():
    """基础表单填写测试"""
    logger = get_logger("examples.form_basic")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # 创建测试页面
            page.set_content(TEST_HTML)
            
            # 等待页面加载
            page.wait_for_selector("#registration-form")
            
            # 填写表单
            page.fill("#username", "testuser123")
            logger.info("已填写用户名")
            
            page.fill("#email", "test@example.com")
            logger.info("已填写邮箱")
            
            page.fill("#password", "password123")
            logger.info("已填写密码")
            
            page.fill("#confirm-password", "password123")
            logger.info("已填写确认密码")
            
            # 选择下拉框
            page.select_option("#gender", "male")
            logger.info("已选择性别")
            
            # 勾选复选框
            page.check("#hobby-reading")
            page.check("#hobby-travel")
            logger.info("已选择兴趣爱好")
            
            # 填写文本域
            page.fill("#bio", "这是一段测试用的个人简介")
            logger.info("已填写个人简介")
            
            # 勾选同意条款
            page.check("#terms")
            logger.info("已勾选服务条款")
            
            # 点击提交
            page.click("#submit-btn")
            logger.info("已点击提交按钮")
            
            # 等待并验证成功消息
            page.wait_for_selector("#success-message:not([style*='display: none'])")
            success_message = page.text_content("#success-message")
            
            assert "注册成功" in success_message
            print("✅ 基础表单测试通过!")
            
        finally:
            browser.close()


# 测试2: 表单验证
def test_form_validation():
    """表单验证测试"""
    logger = get_logger("examples.form_validation")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            page.set_content(TEST_HTML)
            page.wait_for_selector("#registration-form")
            
            # 不填写任何内容直接提交
            page.click("#submit-btn")
            
            # 验证错误消息
            username_error = page.text_content("#username-error")
            assert "用户名不能为空" in username_error
            
            email_error = page.text_content("#email-error")
            assert "邮箱" in email_error or "email" in email_error.lower()
            
            logger.info("表单验证测试通过")
            print("✅ 表单验证测试通过!")
            
        finally:
            browser.close()


# 测试3: 密码不匹配验证
def test_password_mismatch():
    """密码不匹配验证测试"""
    logger = get_logger("examples.password_mismatch")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            page.set_content(TEST_HTML)
            page.wait_for_selector("#registration-form")
            
            # 填写表单，密码不匹配
            page.fill("#username", "testuser")
            page.fill("#email", "test@example.com")
            page.fill("#password", "password123")
            page.fill("#confirm-password", "password456")  # 不匹配
            page.click("#terms")
            
            page.click("#submit-btn")
            
            # 验证错误消息
            confirm_error = page.text_content("#confirm-password-error")
            assert "不一致" in confirm_error
            
            logger.info("密码验证测试通过")
            print("✅ 密码验证测试通过!")
            
        finally:
            browser.close()


# 测试4: 重置表单
def test_form_reset():
    """表单重置测试"""
    logger = get_logger("examples.form_reset")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            page.set_content(TEST_HTML)
            page.wait_for_selector("#registration-form")
            
            # 填写表单
            page.fill("#username", "testuser")
            page.fill("#email", "test@example.com")
            page.fill("#password", "password123")
            
            # 点击重置
            page.click("#reset-btn")
            
            # 验证表单已清空
            username_value = page.input_value("#username")
            email_value = page.input_value("#email")
            
            assert username_value == ""
            assert email_value == ""
            
            logger.info("表单重置测试通过")
            print("✅ 表单重置测试通过!")
            
        finally:
            browser.close()


# 测试5: 使用BasePage类
def test_form_with_base_page():
    """使用BasePage类的表单测试"""
    logger = get_logger("examples.form_base_page")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            base_page = BasePage(page)
            
            # 加载页面
            base_page._page.set_content(TEST_HTML)
            base_page.wait_for_selector("#registration-form")
            
            # 使用BasePage方法填写表单
            base_page.fill("#username", "automationuser")
            base_page.fill("#email", "auto@test.com")
            base_page.fill("#password", "test123456")
            base_page.fill("#confirm-password", "test123456")
            base_page.select_option("#gender", "female")
            base_page.check("#hobby-sports")
            base_page.fill("#bio", "使用BasePage进行自动化测试")
            base_page.check("#terms")
            
            # 提交
            base_page.click("#submit-btn")
            
            # 验证
            success_visible = base_page.is_visible("#success-message")
            assert success_visible
            
            print("✅ BasePage表单测试通过!")
            
        finally:
            browser.close()


if __name__ == "__main__":
    # 运行单个测试
    test_form_basic_fill()
