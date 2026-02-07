import os
import re
import json
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple


class SDKLogDecryptor:
    """SDK日志解密工具类"""

    def __init__(self, fix_chinese: bool = True, extract_json: bool = True):
        """
        初始化解密器

        Args:
            fix_chinese: 是否修复中文字符乱码
            extract_json: 是否提取并格式化JSON
        """
        self.fix_chinese = fix_chinese
        self.extract_json = extract_json

    def fix_chinese_text(self, text: str) -> str:
        """修复中文字符乱码"""
        if not text or not self.fix_chinese:
            return text

        # 常见的乱码修复
        fixes = [
            ('鎴成功姛', '成功'),
            ('鎴成姛', '成'),
            ('鎴功姛', '功'),
            ('鎴', ''),
            ('姛', ''),
            ('愬', '成功'),
            ('愭', '失败'),
            ('応', '成'),
            ('憃', '败'),
            ('Ɂŀ̀', ''),  # 特殊乱码
        ]

        # 控制字符修复
        control_chars = [chr(i) for i in range(32) if i not in [9, 10, 13]]  # 排除\t, \n, \r
        for char in control_chars:
            fixes.append((char, ''))

        result = text
        for wrong, correct in fixes:
            result = result.replace(wrong, correct)

        # 修复JSON中的msg字段
        result = re.sub(r'"msg"\s*:\s*"鎴成功姛"', '"msg":"成功"', result)
        result = re.sub(r'"msg"\s*:\s*"愬"', '"msg":"成功"', result)
        result = re.sub(r'"msg"\s*:\s*"愭"', '"msg":"失败"', result)
        result = re.sub(r'"msg"\s*:\s*""', '"msg":"成功"', result)

        # 修复其他常见问题
        result = result.replace('nstall', 'Install')
        result = result.replace('nternet', 'Internet')
        result = result.replace('nitSdk', 'InitSdk')
        result = result.replace('IInstall', 'Install')  # 修复重复的I

        return result

    def xor_decrypt_bytes(self, data_bytes: bytes) -> bytes:
        """异或解密字节数据"""
        result = bytearray()
        for byte in data_bytes:
            result.append(byte ^ 67)  # XOR with 'C'
        return bytes(result)

    def decrypt_line_simple(self, line: str) -> str:
        """解密单行文本"""
        try:
            # 将文本转为字节
            try:
                line_bytes = line.encode('utf-8')
            except:
                line_bytes = line.encode('latin-1', errors='ignore')

            # 异或解密
            decrypted_bytes = self.xor_decrypt_bytes(line_bytes)

            # 尝试多种编码解码
            encodings = ['utf-8', 'gbk', 'latin-1', 'cp1252']

            for encoding in encodings:
                try:
                    result = decrypted_bytes.decode(encoding, errors='strict')
                    # 如果解码成功，修复中文
                    result = self.fix_chinese_text(result)
                    return result
                except:
                    continue

            # 如果都不行，使用utf-8忽略错误
            result = decrypted_bytes.decode('utf-8', errors='ignore')
            result = self.fix_chinese_text(result)
            return result

        except Exception as e:
            return f"[解密失败: {str(e)[:30]}]"

    def is_encrypted_line(self, line: str) -> bool:
        """判断一行是否加密"""
        if not line.strip():
            return False

        # 检查控制字符（除了常见的换行、制表符）
        control_chars = 0
        for c in line[:100]:
            code = ord(c)
            if code < 32 and code not in [9, 10, 13]:  # 排除\t, \n, \r
                control_chars += 1

        if control_chars > 0:
            return True

        # 检查高位字节比例
        high_chars = sum(1 for c in line[:100] if ord(c) > 127)
        if len(line[:100]) > 0 and high_chars / len(line[:100]) > 0.3:
            return True

        return False

    def extract_json_from_text(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取JSON对象"""
        json_objects = []

        # 查找所有可能的JSON
        start = 0
        while start < len(text):
            json_start = text.find('{', start)
            if json_start == -1:
                break

            # 尝试解析JSON
            try:
                # 找到匹配的右括号
                brace_count = 0
                in_string = False
                escape = False
                json_end = -1

                for i in range(json_start, len(text)):
                    char = text[i]

                    if escape:
                        escape = False
                        continue

                    if char == '\\':
                        escape = True
                    elif char == '"':
                        in_string = not in_string
                    elif not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break

                if json_end != -1:
                    json_str = text[json_start:json_end]
                    try:
                        json_obj = json.loads(json_str)
                        # 格式化JSON
                        formatted_json = json.dumps(json_obj, ensure_ascii=False, indent=2)
                        json_objects.append({
                            'start': json_start,
                            'end': json_end,
                            'original': json_str,
                            'formatted': formatted_json,
                            'object': json_obj
                        })
                        start = json_end
                    except json.JSONDecodeError:
                        start = json_start + 1
                else:
                    start = json_start + 1

            except Exception:
                start = json_start + 1

        return json_objects

    def decrypt_text(self, text: str) -> str:
        """
        解密文本

        Args:
            text: 要解密的文本

        Returns:
            解密后的文本
        """
        lines = text.split('\n')
        decrypted_lines = []

        for line in lines:
            if not line.strip():
                decrypted_lines.append("")
                continue

            # 判断是否加密
            is_encrypted = self.is_encrypted_line(line)

            if is_encrypted:
                # 解密这一行
                decrypted = self.decrypt_line_simple(line)
                decrypted_lines.append(decrypted)
            else:
                # 已经是明文
                decrypted_lines.append(line)

        return '\n'.join(decrypted_lines)

    def format_with_json(self, text: str) -> str:
        """
        格式化输出，提取JSON

        Args:
            text: 要格式化的文本

        Returns:
            格式化后的文本
        """
        if not self.extract_json:
            return text

        # 提取JSON
        json_objects = self.extract_json_from_text(text)

        if not json_objects:
            return text

        # 构建输出
        output = text + "\n\n" + "=" * 60 + "\n"
        output += "提取的JSON数据:\n" + "=" * 60 + "\n\n"

        for i, json_obj in enumerate(json_objects):
            output += f"JSON #{i + 1} (位置: {json_obj['start']}-{json_obj['end']}):\n"
            output += json_obj['formatted'] + "\n\n"

        return output

    def decrypt_with_metadata(self, text: str) -> Dict[str, Any]:
        """
        解密文本并返回包含元数据的完整结果

        Args:
            text: 要解密的文本

        Returns:
            包含解密结果和元数据的字典
        """
        # 解密文本
        decrypted_text = self.decrypt_text(text)

        # 格式化输出（提取JSON）
        formatted_text = self.format_with_json(decrypted_text)

        # 提取JSON对象
        json_objects = self.extract_json_from_text(decrypted_text)

        # 添加头部信息
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines_count = len(text.split('\n'))

        header = f"=== SDK日志解密结果 ===\n"
        header += f"解密时间: {timestamp}\n"
        header += f"总行数: {lines_count}\n"
        header += f"修复中文: {'是' if self.fix_chinese else '否'}\n"
        header += f"提取JSON: {'是' if self.extract_json else '否'}\n"
        header += f"发现JSON对象: {len(json_objects)} 个\n"
        header += "=" * 60 + "\n\n"

        final_result = header + formatted_text

        return {
            'success': True,
            'timestamp': timestamp,
            'original_length': len(text),
            'decrypted_length': len(decrypted_text),
            'line_count': lines_count,
            'json_count': len(json_objects),
            'result': final_result,
            'decrypted_text': decrypted_text,
            'json_objects': json_objects,
            'metadata': {
                'fix_chinese': self.fix_chinese,
                'extract_json': self.extract_json
            }
        }

    def decrypt_file(self, file_path: str) -> Dict[str, Any]:
        """
        解密文件

        Args:
            file_path: 文件路径

        Returns:
            包含解密结果和元数据的字典
        """
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 解密内容
            result = self.decrypt_with_metadata(content)

            # 添加文件信息
            result['file_info'] = {
                'file_name': os.path.basename(file_path),
                'file_size': os.path.getsize(file_path),
                'file_path': file_path
            }

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }

    def save_result(self, result: str, output_path: Optional[str] = None) -> str:
        """
        保存解密结果到文件

        Args:
            result: 要保存的文本
            output_path: 输出文件路径，如果为None则自动生成

        Returns:
            保存的文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"decrypted_{timestamp}.txt"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)

        return output_path


# 使用示例
if __name__ == "__main__":
    # 创建解密器实例
    decryptor = SDKLogDecryptor(fix_chinese=True, extract_json=True)

    # 示例1: 解密文本
    encrypted_text = "你的加密文本..."
    result = decryptor.decrypt_with_metadata(encrypted_text)
    print(f"解密成功: {result['success']}")
    print(f"解密行数: {result['line_count']}")
    print(f"发现JSON: {result['json_count']}个")

    # 保存结果
    saved_path = decryptor.save_result(result['result'])
    print(f"结果已保存到: {saved_path}")

    # 示例2: 解密文件
    file_result = decryptor.decrypt_file("encrypted.log")
    if file_result['success']:
        print(f"文件解密成功: {file_result['file_info']['file_name']}")
        print(f"文件大小: {file_result['file_info']['file_size']}字节")
    else:
        print(f"文件解密失败: {file_result['error']}")


    # 示例3: 批量解密
    def batch_decrypt_files(file_list: List[str], output_dir: str = "output"):
        """批量解密文件"""
        os.makedirs(output_dir, exist_ok=True)

        results = []
        for file_path in file_list:
            print(f"正在解密: {file_path}")
            result = decryptor.decrypt_file(file_path)

            if result['success']:
                # 保存解密结果
                filename = os.path.basename(file_path)
                output_path = os.path.join(output_dir, f"decrypted_{filename}")
                decryptor.save_result(result['result'], output_path)
                results.append((file_path, True, output_path))
            else:
                results.append((file_path, False, result['error']))

        return results