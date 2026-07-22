"""
加密解密工具模块
整合SDK日志解密相关的工具函数
"""
import re
import json
from datetime import datetime
from typing import Optional, Dict, List, Any


class CryptoUtils:
    """加密解密工具类"""
    
    @staticmethod
    def swap_high_low_bits(byte_value: int) -> int:
        """
        交换字节的高4位和低4位
        
        Args:
            byte_value: 字节值(0-255)
            
        Returns:
            交换后的字节值
        """
        high_nibble = (byte_value & 0xF0) >> 4
        low_nibble = byte_value & 0x0F
        return (low_nibble << 4) | high_nibble
    
    @staticmethod
    def xor_decrypt_bytes(data_bytes: bytes, xor_key: int = 67) -> bytes:
        """
        使用XOR进行字节解密
        
        Args:
            data_bytes: 要解密的字节数据
            xor_key: XOR密钥(默认67 = 'C')
            
        Returns:
            解密后的字节数据
        """
        return bytes(byte ^ xor_key for byte in data_bytes)
    
    @staticmethod
    def calculate_text_score(text: str) -> int:
        """
        计算文本的可读性得分
        用于判断解密是否成功
        
        Args:
            text: 要评分的文本
            
        Returns:
            可读性得分(越高越可读)
        """
        if not text or len(text) == 0:
            return 0
        
        score = 0
        
        # 检查中文字符(权重5)
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fa5')
        score += chinese_chars * 5
        
        # 检查英文字母(权重2)
        english_chars = sum(1 for c in text if 'a' <= c <= 'z' or 'A' <= c <= 'Z')
        score += english_chars * 2
        
        # 检查数字(权重2)
        digit_chars = sum(1 for c in text if '0' <= c <= '9')
        score += digit_chars * 2
        
        # 检查空白字符(权重1)
        space_chars = sum(1 for c in text if c in ' \t\n\r')
        score += space_chars
        
        # 检查标点符号(权重2)
        punctuation_chars = sum(1 for c in text if c in ',.!?;:')
        score += punctuation_chars * 2
        
        # 检查常见中文词语(每个词+10分)
        common_chinese_words = ['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一']
        for word in common_chinese_words:
            if word in text:
                score += 10
        
        # 检查常见英文单词(每个词+8分)
        common_english_words = ['the', 'and', 'you', 'that', 'this', 'for', 'are', 'have', 'was', 'with']
        for word in common_english_words:
            if word in text.lower():
                score += 8
        
        # 检查JSON结构(+20分)
        if '{' in text and '}' in text and ':' in text:
            score += 20
        
        # 检查日志格式(每个关键词+15分)
        log_keywords = ['error', 'info', 'debug', 'warn', 'exception', 'log']
        for keyword in log_keywords:
            if keyword in text.lower():
                score += 15
        
        # 惩罚乱码字符(权重-10)
        garbage_chars = sum(1 for c in text if ord(c) < 32 and c not in '\t\n\r')
        score -= garbage_chars * 10
        
        # 惩罚替换字符(权重-5)
        replacement_chars = text.count('�') + text.count('?')
        score -= replacement_chars * 5
        
        return max(0, score)


class TextCleaner:
    """文本清理工具类"""
    
    # 常见乱码映射表
    GARBLED_TEXT_MAP = {
        '鎴成功姛': '成功',
        '鎴成姛': '成',
        '鎴功姛': '功',
        '鎴': '',
        '姛': '',
        '愬': '成功',
        '愭': '失败',
        '応': '成',
        '憃': '败',
        'Ɂŀ̀': '',
        'nstall': 'Install',
        'nternet': 'Internet',
        'nitSdk': 'InitSdk',
        'IInstall': 'Install',
    }
    
    @classmethod
    def fix_chinese_text(cls, text: str) -> str:
        """
        修复中文字符乱码
        
        Args:
            text: 要修复的文本
            
        Returns:
            修复后的文本
        """
        if not text:
            return text
        
        result = text
        
        # 应用乱码映射表
        for wrong, correct in cls.GARBLED_TEXT_MAP.items():
            result = result.replace(wrong, correct)
        
        # 移除控制字符(保留\t, \n, \r)
        control_chars = [chr(i) for i in range(32) if i not in [9, 10, 13]]
        for char in control_chars:
            result = result.replace(char, '')
        
        # 修复JSON中的msg字段
        result = re.sub(r'"msg"\s*:\s*"鎴成功姛"', '"msg":"成功"', result)
        result = re.sub(r'"msg"\s*:\s*"愬"', '"msg":"成功"', result)
        result = re.sub(r'"msg"\s*:\s*"愭"', '"msg":"失败"', result)
        result = re.sub(r'"msg"\s*:\s*""', '"msg":"成功"', result)
        
        return result
    
    @staticmethod
    def remove_control_chars(text: str) -> str:
        """移除文本中的控制字符"""
        return ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')


class JSONExtractor:
    """JSON提取和格式化工具类"""
    
    @staticmethod
    def extract_json_from_text(text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取所有JSON对象
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            提取的JSON对象列表
        """
        json_objects = []
        start = 0
        
        while start < len(text):
            json_start = text.find('{', start)
            if json_start == -1:
                break
            
            # 查找匹配的右括号
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
        
        return json_objects
    
    @staticmethod
    def format_json_objects(json_objects: List[Dict[str, Any]]) -> str:
        """
        格式化JSON对象列表为可读文本
        
        Args:
            json_objects: JSON对象列表
            
        Returns:
            格式化后的文本
        """
        if not json_objects:
            return ""
        
        output = "\n" + "=" * 60 + "\n"
        output += "📋 提取的JSON数据:\n" + "=" * 60 + "\n\n"
        
        for i, json_obj in enumerate(json_objects, 1):
            output += f"JSON #{i} (位置: {json_obj['start']}-{json_obj['end']}):\n"
            output += json_obj['formatted'] + "\n\n"
        
        return output
