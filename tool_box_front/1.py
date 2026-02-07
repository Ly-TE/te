def swap_high_low_bits(c):
    """交换字节的高4位和低4位"""
    high_nibble = (c & 0xF0) >> 4
    low_nibble = c & 0x0F
    return (low_nibble << 4) | high_nibble


def calculate_text_score(text):
    """计算文本的可读性得分"""
    if not text or len(text) == 0:
        return 0

    score = 0

    # 检查中文字符
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fa5')
    score += chinese_chars * 5

    # 检查英文字母
    english_chars = sum(1 for c in text if 'a' <= c <= 'z' or 'A' <= c <= 'Z')
    score += english_chars * 2

    # 检查数字
    digit_chars = sum(1 for c in text if '0' <= c <= '9')
    score += digit_chars * 2

    # 检查空白字符
    space_chars = sum(1 for c in text if c in ' \t\n\r')
    score += space_chars * 1

    # 检查标点符号
    punctuation_chars = sum(1 for c in text if c in ',.!?;:')
    score += punctuation_chars * 2

    # 检查常见中文词语
    common_chinese_words = ['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一']
    for word in common_chinese_words:
        if word in text:
            score += 10

    # 检查常见英文单词
    common_english_words = ['the', 'and', 'you', 'that', 'this', 'for', 'are', 'have', 'was', 'with']
    for word in common_english_words:
        if word in text.lower():
            score += 8

    # 检查JSON结构
    if '{' in text and '}' in text and ':' in text:
        score += 20

    # 检查日志格式
    log_keywords = ['error', 'info', 'debug', 'warn', 'exception', 'log']
    for keyword in log_keywords:
        if keyword in text.lower():
            score += 15

    # 惩罚乱码字符
    garbage_chars = sum(1 for c in text if ord(c) < 32 and c not in '\t\n\r')
    score -= garbage_chars * 10

    # 惩罚替换字符
    replacement_chars = text.count('�') + text.count('?')
    score -= replacement_chars * 5

    return max(0, score)


def analyze_improved():
    print("=== 深入分析解密算法 ===\n")

    encrypted_text = "鯜`慇 A@朽p朽P馈  P朅鯬 繮`鄍@@衊A朅?e5朅鰰U榨DD郹Pp朅鉇AAAA"

    try:
        encrypted_bytes = encrypted_text.encode('gbk')
    except:
        encrypted_bytes = encrypted_text.encode('utf-8')

    print(f"分析 {len(encrypted_bytes)} 字节数据\n")

    # 尝试不同的XOR值组合
    print("=== 尝试不同XOR值和算法组合 ===")

    # 常见XOR值
    common_xor_values = [67, 88, 0x55, 0xAA, 0xFF, 0x33, 0xCC, 0x66, 0x99, 0x5A]

    best_results = []

    for xor_val in common_xor_values:
        # 算法1：先XOR，再交换
        result1_bytes = [swap_high_low_bits(b ^ xor_val) for b in encrypted_bytes[:50]]

        # 算法2：先交换，再XOR
        result2_bytes = [swap_high_low_bits(b) ^ xor_val for b in encrypted_bytes[:50]]

        # 尝试解码
        for encoding in ['gbk', 'utf-8', 'latin-1']:
            try:
                # 算法1结果
                text1 = bytes(result1_bytes).decode(encoding, errors='ignore')
                score1 = calculate_text_score(text1)

                if score1 > 20:
                    best_results.append({
                        'algorithm': f"先XOR 0x{xor_val:02x}再交换",
                        'xor': xor_val,
                        'encoding': encoding,
                        'score': score1,
                        'preview': text1[:80]
                    })

                # 算法2结果
                text2 = bytes(result2_bytes).decode(encoding, errors='ignore')
                score2 = calculate_text_score(text2)

                if score2 > 20:
                    best_results.append({
                        'algorithm': f"先交换再XOR 0x{xor_val:02x}",
                        'xor': xor_val,
                        'encoding': encoding,
                        'score': score2,
                        'preview': text2[:80]
                    })

            except:
                continue

    # 按分数排序
    best_results.sort(key=lambda x: x['score'], reverse=True)

    print(f"\n找到 {len(best_results)} 个可能的结果\n")

    # 显示前10个
    for i, result in enumerate(best_results[:10]):
        print(f"{i + 1}. 算法: {result['algorithm']}")
        print(
            f"   XOR值: {result['xor']} (0x{result['xor']:02x}, '{chr(result['xor']) if 32 <= result['xor'] < 127 else 'N/A'}')")
        print(f"   编码: {result['encoding']}, 得分: {result['score']}")
        print(f"   预览: {result['preview']}")
        print()

    # 检查原始数据特征
    print("\n=== 原始数据特征 ===")
    print(f"字节范围: {min(encrypted_bytes)} - {max(encrypted_bytes)}")

    # 统计高位字节(>127)比例
    high_bytes = sum(1 for b in encrypted_bytes if b > 127)
    print(f"高位字节比例: {high_bytes / len(encrypted_bytes) * 100:.1f}%")

    # 检查常见模式
    print("\n=== 字节频率分析 ===")
    freq = {}
    for b in encrypted_bytes:
        freq[b] = freq.get(b, 0) + 1

    top_10 = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
    for byte, count in top_10:
        print(f"字节 0x{byte:02x} ({byte:3d}): {count:3d}次 ({count / len(encrypted_bytes) * 100:.1f}%)")

    # 特别测试XOR 67（'C'）
    print("\n=== 特别测试 XOR 67 ('C') ===")
    xor_val = 67

    # 算法1：先XOR 67，再交换
    algo1_bytes = [swap_high_low_bits(b ^ xor_val) for b in encrypted_bytes[:100]]

    # 算法2：先交换，再XOR 67
    algo2_bytes = [swap_high_low_bits(b) ^ xor_val for b in encrypted_bytes[:100]]

    print(f"\n算法1（先XOR {xor_val}再交换）:")
    for encoding in ['gbk', 'utf-8', 'latin-1']:
        try:
            text = bytes(algo1_bytes).decode(encoding, errors='ignore')
            score = calculate_text_score(text[:100])
            print(f"  {encoding}: 得分={score}, 预览={text[:80]}")
        except:
            pass

    print(f"\n算法2（先交换再XOR {xor_val}）:")
    for encoding in ['gbk', 'utf-8', 'latin-1']:
        try:
            text = bytes(algo2_bytes).decode(encoding, errors='ignore')
            score = calculate_text_score(text[:100])
            print(f"  {encoding}: 得分={score}, 预览={text[:80]}")
        except:
            pass


# 运行分析
if __name__ == "__main__":
    analyze_improved()