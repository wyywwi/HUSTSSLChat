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

server_name = get_common_name("../certs/server/server.crt")
context = create_tls_context("../certs/server/server.crt", "../certs/server/server.key", "../certs/ca/ca.crt", server_side=True)

print(f"Your username is {server_name}. Please run ../certs/cert_generate.sh to change it.")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 8081))
server_socket.listen(5)
print(f"Server '{server_name}' running on 0.0.0.0:8081...")

# 用于保存当前聊天连接
current_conn = None
current_client_name = None

def handle_client(conn, addr):
    global current_state, current_conn, current_client_name
    ssl_conn = SSL.Connection(context, conn)
    ssl_conn.set_accept_state()
    ssl_conn.do_handshake()
    print(f"Connection established with {addr}")

    # 握手阶段：接收聊天请求
    try:
        # 接收客户端发送的握手请求，包含客户端名称
        data = ssl_conn.recv(1024).decode()
        if data.startswith("CHAT_REQUEST"):
            client_name = data.split("|")[1]
            # 提示服务器是否接受聊天请求
            accept = input(f"Client '{client_name}' wants to chat. Accept? (y/n): ").strip().lower()
            if accept == 'y':
                ssl_conn.send(f"ACCEPT|{server_name}".encode())
                current_state = CHAT
                current_conn = ssl_conn
                current_client_name = client_name
                chat_session(ssl_conn, client_name)
            else:
                ssl_conn.send(b"REJECT")
                ssl_conn.shutdown()
                ssl_conn.close()
        else:
            ssl_conn.send(b"INVALID_REQUEST")
            ssl_conn.shutdown()
            ssl_conn.close()
    except Exception as e:
        print(f"Handshake failed: {e}")
        ssl_conn.shutdown()
        ssl_conn.close()

def chat_session(ssl_conn, client_name):
    global current_state, current_conn, current_client_name
    # 使用 curses 构建 TUI
    curses.wrapper(chat_tui, ssl_conn, client_name)

def chat_tui(stdscr, ssl_conn, client_name):
    global current_state, current_conn, current_client_name
    # 初始化 curses 设置
    curses.curs_set(1)
    stdscr.clear()
    stdscr.refresh()

    # 获取屏幕大小
    max_y, max_x = stdscr.getmaxyx()

    # 创建窗口
    header_win = curses.newwin(3, max_x, 0, 0)
    chat_win = curses.newwin(max_y - 6, max_x, 3, 0)
    input_win = curses.newwin(3, max_x, max_y - 3, 0)

    # 显示双方名称
    header_win.addstr(1, 2, f"Chatting with {client_name}")
    header_win.refresh()

    # 聊天记录
    chat_history = []

    # 创建线程接收消息
    def receive_messages():
        nonlocal chat_history
        global current_state
        while current_state == CHAT:
            try:
                msg = ssl_conn.recv(1024)
                if not msg or msg.decode() == "/exit":
                    chat_history.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {client_name} left the chat.")
                    update_chat_window(chat_win, chat_history)
                    current_state = IDLE
                    break
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                chat_history.append(f"[{timestamp}] {client_name}: {msg.decode()}")
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

    # 发送消息循环
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

    # 退出聊天，清理资源
    chat_filename = f"SERVER_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{server_name}_to_{client_name}.log"
    save_encrypted_chat_history(chat_filename, key, chat_history)
    ssl_conn.shutdown()
    ssl_conn.close()
    current_conn = None
    current_client_name = None

# 主循环，接受客户端连接
while True:
    if current_state == IDLE:
        try:
            conn, addr = server_socket.accept()
            if current_conn is None:
                threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
            else:
                # 已经有一个客户端在聊天，拒绝新的连接
                conn.send(b"BUSY")
                conn.close()
        except KeyboardInterrupt:
            break
    else:
        # 当前正在聊天，不接受新的连接
        pass

server_socket.close()
print("Server shut down.")
