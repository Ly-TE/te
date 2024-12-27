# 当然，以下是对前述三种列表去重方法的代码添加注释，以帮助理解各自的工作原理和适用场景：
#
# 使用 set 方法去重：

# python
# 定义一个含有重复元素的列表
my_list = [1, 2, 2, 3, 4, 4, 5]
# 将列表转换为集合来自动去除重复元素，然后再将结果转换回列表
unique_list = list(set(my_list))
# 输出去重后的列表
print(unique_list)  # 输出: [1, 2, 3, 4, 5]
# 这种方法最简单，但会改变元素的原始顺序。
#
# 使用列表推导式和条件语句去重：

python
# 定义一个含有重复元素的列表
my_list = [1, 2, 2, 3, 4, 4, 5]
# 创建一个空列表用于存放不重复的元素
unique_list = []
# 通过列表推导式遍历每个元素，如果该元素尚未在unique_list中，则添加进去
[unique_list.append(x) for x in my_list if x not in unique_list]
# 输出去重后保持原始顺序的列表
print(unique_list)  # 输出: [1, 2, 3, 4, 5]
# 此方法保持了元素的原始顺序，适合需要保留元素添加顺序的情况。
#
# 使用 collections.Counter 方法去重：

python
from collections import Counter

# 定义一个含有重复元素的列表
my_list = [1, 2, 2, 3, 4, 4, 5]
# 使用Counter来统计列表中每个元素的出现次数
counts = Counter(my_list)
# 通过列表推导式从Counter对象中提取所有出现过的元素
unique_list = [x for x in counts if counts[x] >= 1]
# 输出去重后保持原始顺序的列表
print(unique_list)  # 输出: [1, 2, 3, 4, 5]
# 这种方法同样可以保留元素的原始顺序，并且适用于需要计算元素出现次数的场景。
#
# 以上就是对三种列表去重方法的代码加注释版本，希望能帮助您更好地理解每种方法的具体实现和适用场合。



