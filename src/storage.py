import os
import base64
import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from getpass import getpass

CHAT_LOGS_DIR = "../chat_logs"

def generate_key_from_password(password: str, salt: bytes) -> bytes:
    """
    从用户输入的密码生成 AES 密钥。
    :param password: 用户密码
    :param salt: 盐值，用于生成密钥
    :return: AES 密钥
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_message(key: bytes, message: str) -> str:
    """
    使用 AES 加密消息。
    """
    fernet = Fernet(key)
    return fernet.encrypt(message.encode()).decode()

def decrypt_message(key: bytes, encrypted_message: str) -> str:
    """
    使用 AES 解密消息。
    """
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_message.encode()).decode()

def save_encrypted_chat_history(filename: str, key: bytes, history: list):
    """
    保存加密的聊天记录。
    :param filename: 保存的文件名
    :param key: AES 密钥
    :param history: 聊天记录列表
    """
    os.makedirs(CHAT_LOGS_DIR, exist_ok=True)
    filepath = os.path.join(CHAT_LOGS_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            for line in history:
                encrypted_line = encrypt_message(key, line)
                f.write(encrypted_line + "\n")
        print(f"Encrypted chat history saved to {filepath}")
    except Exception as e:
        print(f"Failed to save chat history: {e}")

def load_and_decrypt_chat_history(filepath: str, key: bytes):
    """
    读取并解密聊天记录。
    :param filepath: 文件路径
    :param key: AES 密钥
    :return: 解密后的聊天记录列表
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            encrypted_lines = f.readlines()
        decrypted_lines = [decrypt_message(key, line.strip()) for line in encrypted_lines]
        return decrypted_lines
    except Exception as e:
        print(f"Failed to load or decrypt chat history: {e}")
        return []

if __name__ == "__main__":
    import getpass

    # 输入文件路径和密码
    log_file = input("Enter the path to the encrypted chat log file: ").strip()
    password = getpass.getpass("Enter the password to decrypt the chat log: ")

    # 使用固定盐值生成密钥
    salt = b'SALTSALTSALT'  # 与聊天记录加密时一致
    key = generate_key_from_password(password, salt)

    # 解密并显示聊天记录
    chat_history = load_and_decrypt_chat_history(log_file, key)
    if chat_history:
        print("\nDecrypted Chat History:")
        for line in chat_history:
            print(line)
    else:
        print("No messages to display or failed to decrypt.")