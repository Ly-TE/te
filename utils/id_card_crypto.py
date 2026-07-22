"""身份证加解密工具：zlib + RC4 + Base64。"""
import base64
import zlib


class RC4:
    """RC4 流加密/解密算法实现。"""

    def __init__(self, key: str):
        if not key:
            raise ValueError("密钥不能为空")
        self.key = key.encode("utf-8")

    @staticmethod
    def _ksa(key: bytes) -> list:
        """密钥调度算法。"""
        key_length = len(key)
        state = list(range(256))
        j = 0

        for i in range(256):
            j = (j + state[i] + key[i % key_length]) % 256
            state[i], state[j] = state[j], state[i]

        return state

    @staticmethod
    def _prga(state: list, data_length: int) -> bytes:
        """伪随机生成算法。"""
        i = 0
        j = 0
        key_stream = bytearray()

        for _ in range(data_length):
            i = (i + 1) % 256
            j = (j + state[i]) % 256
            state[i], state[j] = state[j], state[i]
            key_stream.append(state[(state[i] + state[j]) % 256])

        return bytes(key_stream)

    def encrypt(self, plaintext: bytes) -> bytes:
        """加密，RC4 加密和解密使用同一套异或逻辑。"""
        return self._crypt(plaintext)

    def decrypt(self, ciphertext: bytes) -> bytes:
        """解密，RC4 加密和解密使用同一套异或逻辑。"""
        return self._crypt(ciphertext)

    def _crypt(self, data: bytes) -> bytes:
        """加密/解密核心操作。"""
        state = self._ksa(self.key)
        key_stream = self._prga(state, len(data))
        return bytes(data[index] ^ key_stream[index] for index in range(len(data)))


class IdCardCryptoHandler:
    """加解密处理器：明文 <-> zlib <-> RC4 <-> Base64。"""

    def __init__(self, key: str = "id_card"):
        self.rc4 = RC4(key)

    def encrypt(self, plaintext: str) -> str:
        """明文加密为 Base64 密文。"""
        plaintext_bytes = plaintext.encode("utf-8")
        compressed = zlib.compress(plaintext_bytes)
        encrypted = self.rc4.encrypt(compressed)
        return base64.b64encode(encrypted).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Base64 密文解密为明文。"""
        encrypted = base64.b64decode(ciphertext)
        compressed = self.rc4.decrypt(encrypted)
        plaintext_bytes = zlib.decompress(compressed)
        return plaintext_bytes.decode("utf-8")