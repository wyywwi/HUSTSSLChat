from OpenSSL import SSL
from tls_utils import create_tls_context
import socket

from storage import generate_key, encrypt_message, save_encrypted_message

key = generate_key("clientpswd")
log_file = "client_logs.txt"

context = create_tls_context("../certs/client/client.crt", "../certs/client/client.key", "../certs/ca/ca.crt")

client_socket = SSL.Connection(context, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
client_socket.connect(('127.0.0.1', 8080))
print("Connected to server.")

try:
    while True:
        # 发送消息
        client_msg = input("Client: ")
        client_socket.send(client_msg.encode())
        encrypted_msg = encrypt_message(key, client_msg)
        save_encrypted_message(log_file, encrypted_msg)

        # 接收消息
        server_msg = client_socket.recv(1024)
        if not server_msg:
            print("Server disconnected.")
            break
        print(f"Server: {server_msg.decode()}")
        encrypted_msg = encrypt_message(key, server_msg.decode())
        save_encrypted_message(log_file, encrypted_msg)
finally:
    client_socket.close()
