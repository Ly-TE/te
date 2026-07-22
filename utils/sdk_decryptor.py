"""
SDK日志解密器
整合并优化原有的解密逻辑
"""
import os
from datetime import datetime
from typing import Optional, Dict, List, Any

from utils.crypto_utils import CryptoUtils, TextCleaner, JSONExtractor


class SDKLogDecryptor:
    """SDK日志解密工具类"""
    
    # 支持的编码列表
    SUPPORTED_ENCODINGS = ['utf-8', 'gbk', 'gb18030', 'latin-1', 'cp1252']
    
    def __init__(self, fix_chinese: bool = True, extract_json: bool = True, xor_key: int = 67):
        """
        初始化解密器
        
        Args:
            fix_chinese: 是否修复中文字符乱码
            extract_json: 是否提取并格式化JSON
            xor_key: XOR解密密钥(默认67)
        """
        self.fix_chinese = fix_chinese
        self.extract_json = extract_json
        self.xor_key = xor_key
        self.crypto = CryptoUtils()
        self.cleaner = TextCleaner()
        self.json_extractor = JSONExtractor()
    
    def is_encrypted_line(self, line: str) -> bool:
        """
        判断一行文本是否加密
        
        Args:
            line: 要判断的文本行
            
        Returns:
            True表示已加密，False表示明文
        """
        if not line.strip():
            return False
        
        # 检查控制字符(除了\t, \n, \r)
        control_chars = sum(
            1 for c in line[:100] 
            if ord(c) < 32 and c not in '\t\n\r'
        )
        if control_chars > 0:
            return True
        
        # 检查高位字节比例
        sample = line[:100]
        if len(sample) > 0:
            high_chars = sum(1 for c in sample if ord(c) > 127)
            if high_chars / len(sample) > 0.3:
                return True
        
        return False
    
    def decrypt_line(self, line: str) -> str:
        """
        解密单行文本
        
        Args:
            line: 要解密的文本行
            
        Returns:
            解密后的文本
        """
        try:
            # 将文本转为字节
            try:
                line_bytes = line.encode('utf-8')
            except UnicodeEncodeError:
                line_bytes = line.encode('latin-1', errors='ignore')
            
            # XOR解密
            decrypted_bytes = self.crypto.xor_decrypt_bytes(line_bytes, self.xor_key)
            
            # 尝试多种编码解码
            best_result = None
            best_score = 0
            
            for encoding in self.SUPPORTED_ENCODINGS:
                try:
                    result = decrypted_bytes.decode(encoding, errors='strict')
                    score = self.crypto.calculate_text_score(result)
                    
                    if score > best_score:
                        best_score = score
                        best_result = result
                        
                        # 如果得分足够高，提前返回
                        if score > 50:
                            break
                except (UnicodeDecodeError, LookupError):
                    continue
            
            # 如果找到结果，修复中文
            if best_result:
                if self.fix_chinese:
                    best_result = self.cleaner.fix_chinese_text(best_result)
                return best_result
            
            # 如果都不行，使用utf-8忽略错误
            result = decrypted_bytes.decode('utf-8', errors='ignore')
            if self.fix_chinese:
                result = self.cleaner.fix_chinese_text(result)
            return result
            
        except Exception as e:
            return f"[解密失败: {str(e)[:50]}]"
    
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
            if self.is_encrypted_line(line):
                decrypted = self.decrypt_line(line)
                decrypted_lines.append(decrypted)
            else:
                # 已经是明文，但可能需要清理
                if self.fix_chinese:
                    line = self.cleaner.fix_chinese_text(line)
                decrypted_lines.append(line)
        
        return '\n'.join(decrypted_lines)
    
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
        
        # 提取JSON对象
        json_objects = []
        if self.extract_json:
            json_objects = self.json_extractor.extract_json_from_text(decrypted_text)
        
        # 构建输出文本
        formatted_text = decrypted_text
        if json_objects:
            formatted_text += self.json_extractor.format_json_objects(json_objects)
        
        # 生成元数据
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines_count = len(text.split('\n'))
        
        # 添加头部信息
        header = f"{'=' * 60}\n"
        header += f"📄 SDK日志解密结果\n"
        header += f"{'=' * 60}\n"
        header += f"⏰ 解密时间: {timestamp}\n"
        header += f"📊 总行数: {lines_count}\n"
        header += f"🔧 修复中文: {'是' if self.fix_chinese else '否'}\n"
        header += f"📦 提取JSON: {'是' if self.extract_json else '否'}\n"
        header += f"🔍 发现JSON对象: {len(json_objects)} 个\n"
        header += f"{'=' * 60}\n\n"
        
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
                'extract_json': self.extract_json,
                'xor_key': self.xor_key
            }
        }
    
    def decrypt_file(self, file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        解密文件
        
        Args:
            file_path: 文件路径
            encoding: 文件编码(默认utf-8)
            
        Returns:
            包含解密结果和元数据的字典
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': f'文件不存在: {file_path}',
                    'file_path': file_path
                }
            
            # 读取文件
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
            
            # 解密内容
            result = self.decrypt_with_metadata(content)
            
            # 添加文件信息
            result['file_info'] = {
                'file_name': os.path.basename(file_path),
                'file_size': os.path.getsize(file_path),
                'file_path': file_path,
                'encoding': encoding
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
            output_path: 输出文件路径(为None时自动生成)
            
        Returns:
            保存的文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"decrypted_{timestamp}.txt"
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        
        return output_path
    
    def batch_decrypt_files(self, file_list: List[str], output_dir: str = "output") -> List[tuple]:
        """
        批量解密文件
        
        Args:
            file_list: 要解密的文件路径列表
            output_dir: 输出目录
            
        Returns:
            解密结果列表 [(file_path, success, result/error), ...]
        """
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        for file_path in file_list:
            print(f"🔄 正在解密: {file_path}")
            result = self.decrypt_file(file_path)
            
            if result['success']:
                # 保存解密结果
                filename = os.path.basename(file_path)
                output_path = os.path.join(output_dir, f"decrypted_{filename}")
                saved_path = self.save_result(result['result'], output_path)
                results.append((file_path, True, saved_path))
                print(f"✅ 解密成功: {saved_path}")
            else:
                results.append((file_path, False, result['error']))
                print(f"❌ 解密失败: {result['error']}")
        
        return results
