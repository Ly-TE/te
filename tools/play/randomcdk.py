import random
import string


def generate_cdk():
    parts = []
    for _ in range(5):
        part = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=5))
        parts.append(part)
    return '-'.join(parts)


cdk_list = [generate_cdk() for _ in range(20)]
for cdk in cdk_list:
    print(cdk)
