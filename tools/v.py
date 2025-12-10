import json
import random
import string


def generate_random_token(length=20):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))


def generate_large_json():
    # 目标文件大小约为 5M 字节，这里使用 5 * 1024 * 1024
    target_size = 30 * 1024
    data = {
        "device_type": "android",
        "flow": [],
        "gameId": 5,
        "account_token": generate_random_token()
    }
    current_size = len(json.dumps(data))
    while current_size < target_size:
        flow_entry = {
            "bytes": random.randint(1000, 1000000),
            "domain": ''.join(random.choice(string.ascii_lowercase) for _ in range(10)) + ".com",
            "flow_type": random.choice(["HTTP", "TCP", "UDP"]),
            "proxy": random.choice([True])
        }
        data["flow"].append(flow_entry)
        current_size = len(json.dumps(data))
    return data


def main():
    large_json = generate_large_json()
    with open(r"D:\1.txt", "w") as f:
        json.dump(large_json, f, indent=4)


if __name__ == "__main__":
    main()