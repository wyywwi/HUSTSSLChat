#!/bin/bash

# 进入 certs 目录
cd "$(dirname "$0")"

# 文件路径配置
CA_DIR="./ca"
SERVER_DIR="./server"
CLIENT_DIR="./client"
CA_CERT="$CA_DIR/ca.crt"
CA_KEY="$CA_DIR/ca.key"

# 检查 CA 文件是否存在
if [[ ! -f "$CA_CERT" || ! -f "$CA_KEY" ]]; then
  echo "Error: CA certificate or key is missing in $CA_DIR."
  exit 1
fi

# 创建 server 和 client 目录
mkdir -p "$SERVER_DIR"
mkdir -p "$CLIENT_DIR"

# 客户端证书生成
# 从命令行参数获取 CN
if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <CN>"
  exit 1
fi
CN="$1"

# 服务端证书生成
echo "Generating server certificate and key for CN: $CN..."
openssl genrsa -out "$SERVER_DIR/server.key" 2048
openssl req -new -key "$SERVER_DIR/server.key" -out "$SERVER_DIR/server.csr" -subj "/C=CN/ST=Hubei/L=Wuhan/O=HUST/OU=IT/CN=$CN"
openssl x509 -req -in "$SERVER_DIR/server.csr" -CA "$CA_CERT" -CAkey "$CA_KEY" -CAcreateserial -out "$SERVER_DIR/server.crt" -days 365 -sha256
rm -f "$SERVER_DIR/server.csr"

echo "Generating client certificate and key for CN: $CN..."
openssl genrsa -out "$CLIENT_DIR/client.key" 2048
openssl req -new -key "$CLIENT_DIR/client.key" -out "$CLIENT_DIR/client.csr" -subj "/C=CN/ST=Hubei/L=Wuhan/O=HUST/OU=IT/CN=$CN"
openssl x509 -req -in "$CLIENT_DIR/client.csr" -CA "$CA_CERT" -CAkey "$CA_KEY" -CAcreateserial -out "$CLIENT_DIR/client.crt" -days 365 -sha256
rm -f "$CLIENT_DIR/client.csr"

# 清理签名序列文件
rm -f "$CA_DIR/ca.srl"

echo "Certificates generated successfully for CN: $CN."
echo "Server certificates: $SERVER_DIR/server.crt, $SERVER_DIR/server.key"
echo "Client certificates: $CLIENT_DIR/client.crt, $CLIENT_DIR/client.key"
