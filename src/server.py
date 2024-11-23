from OpenSSL import SSL
from tls_utils import create_tls_context
import socket

from storage import generate_key, encrypt_message, save_encrypted_message

key = generate_key("serverpswd")
log_file = "server_logs.txt"

context = create_tls_context("../certs/server/server.crt", "../certs/server/server.key", "../certs/ca/ca.crt", server_side=True)

server_socket = SSL.Connection(context, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
server_socket.bind(('127.0.0.1', 8080))
server_socket.listen(5)
print("Server running on 127.0.0.1:8080...")

client_conn, addr = server_socket.accept()
print(f"Connection established with {addr}")

try:
    while True:
        # 接收消息
        msg = client_conn.recv(1024)
        if not msg:
            print("Client disconnected.")
            break
        print(f"Client: {msg.decode()}")
        encrypted_msg = encrypt_message(key, msg.decode())
        save_encrypted_message(log_file, encrypted_msg)

        # 发送消息
        server_msg = input("Server: ")
        client_conn.send(server_msg.encode())
        encrypted_msg = encrypt_message(key, server_msg)
        save_encrypted_message(log_file, encrypted_msg)
finally:
    client_conn.close()
    server_socket.close()
