# HUSTSSLChat

## 简介

HUSTSSLChat 是一个基于 OpenSSL 实现的安全聊天系统，支持以下功能：

1. **点对点聊天模式**：
   - 支持客户端与服务端的安全通信。
   - 基于 TLS 协议实现数据加密传输，保障数据隐私性。

2. **基于OpenSSL的双向认证通信**：
   - 客户端与服务端使用自签名证书进行双向身份验证。

3. **加密聊天记录**：
   - 聊天记录使用 AES 加密保存到本地，输入正确口令可查看。

4. **Docker 演示环境**：
   - 提供一个包含三台主机的 Docker 内网环境，用于模拟和演示软件功能。

---

## 软件架构

项目的目录结构如下：

```
.
├── certs               # 存放证书生成脚本及生成的证书文件
│   ├── ca              # 自签名 CA 证书及密钥
│   ├── client          # 客户端证书及密钥
│   └── server          # 服务端证书及密钥
├── chat_logs           # 加密聊天记录存储文件夹
├── src                 # 项目源代码
│   ├── client.py       # 客户端代码
│   ├── server.py       # 服务端代码
│   ├── storage.py      # 加密与解密工具
│   └── tls_utils.py    # TLS 上下文工具
├── README.md           # 项目说明文件
└── Makefile            # 自动化工具
```

---

## 使用方法

### 1. 环境准备

- 安装 Python 3.10 及以上版本。
- 安装依赖库：
  ```bash
  pip install cryptography pyopenssl
  ```

### 2. 生成证书

运行 `certs/certs_generate.sh` 生成所需证书：
```bash
bash certs/certs_generate.sh <CN>
```
例如，生成以 `Alice` 为身份的证书：
```bash
bash certs/certs_generate.sh Alice
```

### 3. 启动聊天服务

#### 服务端
进入 `src` 目录，运行以下命令启动服务端：
```bash
python3 server.py
```

#### 客户端
进入 `src` 目录，运行以下命令启动客户端：
```bash
python3 client.py
```

按照界面提示输入服务器 IP 和端口，即可建立连接开始聊天。

### 4. 查看聊天记录

运行以下命令解密查看聊天记录：
```bash
python3 storage.py
```
输入文件路径和解密密码即可查看记录。

---

## Docker 演示环境

### 1. 构建环境
运行以下命令构建三台主机的 Docker 内网环境：
```bash
make setup-docker
```

### 2. 清理环境
运行以下命令清理 Docker 环境：
```bash
make clean-docker
```

### **Makefile 功能说明**

1. **通用入口**：
   - `make certs`：生成证书。
   - `make client`：运行客户端。
   - `make server`：运行服务端。

2. **Docker 环境搭建**：
   - `make setup-docker`：
     - 创建一个 Docker 网络。
     - 构建包含项目源代码的 Docker 镜像。
     - 启动三台主机并将代码复制到主机中。
   - `make clean-docker`：清理 Docker 容器、网络和镜像。