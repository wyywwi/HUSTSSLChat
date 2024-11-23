from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

def generate_key(passphrase):
    """
    使用 PBKDF2 从用户提供的口令生成一个固定的 AES 密钥。
    :param passphrase: 用户输入的口令
    :return: 符合 Fernet 要求的 32 字节密钥
    """
    salt = b'test_salt'  # 盐值
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # Fernet 密钥需要 32 字节
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
    return key

def encrypt_message(key, message):
    """
    加密消息。
    """
    cipher = Fernet(key)
    return cipher.encrypt(message.encode())

def decrypt_message(key, encrypted_message):
    """
    解密消息。
    """
    cipher = Fernet(key)
    return cipher.decrypt(encrypted_message).decode()

def save_encrypted_message(filepath, encrypted_message):
    """
    保存加密消息到文件。
    """
    with open(filepath, "ab") as f:
        f.write(encrypted_message + b'\n')

def load_and_decrypt_messages(filepath, key):
    """
    加载文件中的加密消息并解密。
    """
    messages = []
    with open(filepath, "rb") as f:
        for line in f:
            messages.append(decrypt_message(key, line.strip()))
    return messages

if __name__ == '__main__':
    log_file = input("Enter log file path: ")
    passphrase = input("Enter passphrase: ")

    key = generate_key(passphrase)
    try:
        messages = load_and_decrypt_messages(log_file, key)
        print("\nDecrypted messages:")
        for msg in messages:
            print(msg)
    except Exception as e:
        print(f"Failed to decrypt messages: {e}")