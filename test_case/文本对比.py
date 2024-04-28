import difflib

text1 = """
https://vf-www.leigod.com/m/activitys/AnnualBill2023.html
"""

text2 = """
https://vf-www.leigod.com/m/activitys/AnnualBill2023.html
"""

d = difflib.Differ()
diff = d.compare(text1.splitlines(), text2.splitlines())
print('\n'.join(diff))
