import allure
import pytest

# 定义一个简单的数学计算函数，用于示例测试
def add_numbers(a, b):
    return a + b

# 测试类，用于编写测试用例
@allure.feature("数学计算功能测试")
class TestMathOperations:
    @allure.story("两数相加功能正常")
    def test_addition(self):
        result = add_numbers(3, 5)
        assert result == 8, f"预期结果为 8，实际得到 {result}"
        allure.attach("计算结果详情", f"3 + 5 的结果是 {result}")

    @allure.story("两数相加边界情况测试")
    def test_addition_boundary(self):
        result = add_numbers(-1, 1)
        assert result == 0, f"预期结果为 0，实际得到 {result}"
        allure.attach("边界计算结果详情", f"-1 + 1 的结果是 {result}")


if __name__ == "__main__":
    pytest.main(["-s", "--alluredir", "allure-results"])