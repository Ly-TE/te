from flask import Flask, request, jsonify, send_from_directory
from Crypto.Cipher import AES
import base64
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

# ========== 根路由：返回HTML页面 ==========
@app.route('/')
def index():
    return send_from_directory('../../tools/play/static', 'index.html')

# ========== 静态文件服务 ==========
@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('../../tools/play/static', filename)

# ========== 原有业务逻辑 ==========
app.config['JSON_AS_ASCII'] = False

def validate_key_length(key):
    if len(key) not in [16, 24, 32]:
        raise ValueError("Key must be 16, 24, or 32 bytes long")
    return True

def encrypt_numbers(numbers, key):
    validate_key_length(key)
    str_num = str(numbers)
    numbers_bytes = str_num.encode('utf-8')

    padding_length = 16 - (len(numbers_bytes) % 16)
    numbers_bytes += bytes([padding_length] * padding_length)

    cipher = AES.new(key, AES.MODE_ECB)
    encrypted_numbers = cipher.encrypt(numbers_bytes)

    return base64.b64encode(encrypted_numbers).decode('utf-8')

def decrypt_numbers(encrypted_result_str, key):
    validate_key_length(key)

    try:
        encrypted_result_bytes = base64.b64decode(encrypted_result_str)
        cipher = AES.new(key, AES.MODE_ECB)
        decrypted_numbers_bytes = cipher.decrypt(encrypted_result_bytes)

        padding_length = decrypted_numbers_bytes[-1]
        decrypted_numbers_bytes1 = decrypted_numbers_bytes[:-padding_length]

        decrypted_number = decrypted_numbers_bytes1.decode('utf-8')
        return decrypted_number
    except Exception as e:
        return None

@app.route('/encrypt', methods=['POST'])
def encrypt_route():
    data = request.get_json()
    numbers_to_encrypt = data.get('numbers')
    encryption_key = b'leigod0123456789'

    try:
        encrypted_result = encrypt_numbers(numbers_to_encrypt, encryption_key)
        return jsonify({'encryptedResult': encrypted_result})
    except ValueError as ve:
        return jsonify({'error': '加密失败，请检查密钥长度是否正确。'})
    except Exception as e:
        return jsonify({'error': '加密过程出现未知错误，请检查输入数据或其他设置。'})

@app.route('/decrypt', methods=['POST'])
def decrypt_route():
    data = request.get_json()
    encrypted_result_str = data.get('encryptedResult')
    encryption_key = b'leigod0123456789'

    decrypted_result = decrypt_numbers(encrypted_result_str, encryption_key)
    if decrypted_result is not None:
        return decrypted_result
    else:
        return jsonify({'error': '解密失败，请检查输入数据或密钥是否正确。'})

if __name__ == '__main__':
    app.run(host='10.1.3.160', port=5000, debug=True)