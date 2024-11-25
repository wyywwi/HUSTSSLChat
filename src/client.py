import socket
import threading
import datetime
import curses
from OpenSSL import SSL
from tls_utils import create_tls_context, get_common_name
from storage import generate_key_from_password, save_encrypted_chat_history
from getpass import getpass

# 定义全局状态
IDLE = 'IDLE'
CHAT = 'CHAT'
current_state = IDLE

password = getpass("Enter a password to encrypt chat logs: ")
salt = b'SALTSALTSALT'
key = generate_key_from_password(password, salt)

client_name = get_common_name("../certs/client/client.crt")
context = create_tls_context("../certs/client/client.crt", "../certs/client/client.key", "../certs/ca/ca.crt")

print(f"Your username is {client_name}. Please run ../certs/cert_generate.sh to change it.")

def chat_tui(stdscr, ssl_conn, server_name):
    global current_state
    curses.curs_set(1)
    stdscr.clear()
    stdscr.refresh()

    max_y, max_x = stdscr.getmaxyx()

    header_win = curses.newwin(3, max_x, 0, 0)
    chat_win = curses.newwin(max_y - 6, max_x, 3, 0)
    input_win = curses.newwin(3, max_x, max_y - 3, 0)

    header_win.addstr(1, 2, f"Chatting with {server_name}")
    header_win.refresh()

    chat_history = []

    def receive_messages():
        nonlocal chat_history
        global current_state
        while current_state == CHAT:
            try:
                msg = ssl_conn.recv(1024)
                if not msg or msg.decode() == "/exit":
                    chat_history.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {server_name} left the chat.")
                    update_chat_window(chat_win, chat_history)
                    current_state = IDLE
                    break
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                chat_history.append(f"[{timestamp}] {server_name}: {msg.decode()}")
                update_chat_window(chat_win, chat_history)
            except Exception as e:
                chat_history.append(f"Error receiving message: {e}")
                break

    def update_chat_window(win, history):
        win.clear()
        start_line = max(0, len(history) - (max_y - 6))
        for idx, line in enumerate(history[start_line:]):
            win.addstr(idx, 0, line)
        win.refresh()

    recv_thread = threading.Thread(target=receive_messages, daemon=True)
    recv_thread.start()

    while current_state == CHAT:
        input_win.clear()
        input_win.addstr(1, 2, "You: ")
        input_win.refresh()
        curses.echo()
        msg = input_win.getstr(1, 6, max_x - 8).decode().strip()
        curses.noecho()
        if msg == "/exit":
            ssl_conn.send(b"/exit")
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            chat_history.append(f"[{timestamp}] You: {msg}")
            update_chat_window(chat_win, chat_history)
            current_state = IDLE
            break
        elif msg:
            try:
                ssl_conn.send(msg.encode())
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                chat_history.append(f"[{timestamp}] You: {msg}")
                update_chat_window(chat_win, chat_history)
            except Exception as e:
                chat_history.append(f"Error sending message: {e}")
                break

    chat_filename = f"CLIENT_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{server_name}_to_{client_name}.log"
    save_encrypted_chat_history(chat_filename, key, chat_history)
    ssl_conn.shutdown()
    ssl_conn.close()

def start_chat(ip, port):
    global current_state
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, port))
    ssl_conn = SSL.Connection(context, client_socket)
    ssl_conn.set_connect_state()
    ssl_conn.do_handshake()

    # 发送聊天请求
    ssl_conn.send(f"CHAT_REQUEST|{client_name}".encode())
    response = ssl_conn.recv(1024).decode()
    if response.startswith("ACCEPT"):
        current_state = CHAT
        server_name = response.split("|")[1]
        curses.wrapper(chat_tui, ssl_conn, server_name)
    elif response == "REJECT":
        print("Chat request was rejected by the server.")
        ssl_conn.shutdown()
        ssl_conn.close()
    elif response == "BUSY":
        print("Server is busy with another client.")
        ssl_conn.shutdown()
        ssl_conn.close()
    else:
        print("Invalid response from server.")
        ssl_conn.shutdown()
        ssl_conn.close()

# 主循环，非聊天状态下输入服务器信息
while True:
    if current_state == IDLE:
        ip = input("Enter server IP (or 'exit' to quit): ").strip()
        if ip.lower() == 'exit':
            break
        port = input("Enter server port: ").strip()
        try:
            port = int(port)
            start_chat(ip, port)
        except Exception as e:
            print(f"Failed to start chat: {e}")
    else:
        pass

print("Client shut down.")
