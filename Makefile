# 通用变量
SRC_DIR = ./src
CERTS_DIR = ./certs
CHAT_LOGS_DIR = ./chat_logs
DOCKER_NETWORK = hustsslchat_network
DOCKER_IMAGE = dockerpull.org/python:3.10
CUSTOM_IMAGE = hustsslchat:latest
TEMP_CONTAINER = hustsslchat_temp
PYTHON_REQUIREMENTS = requirements.txt
TMUX_SESSION = hustsslchat
DOCKER_CONTAINERS = host1 host2 host3

# 默认目标
all:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  certs          - Generate certificates"
	@echo "  client         - Run the client application"
	@echo "  server         - Run the server application"
	@echo "  setup-docker   - Set up a Docker environment with three hosts"
	@echo "  clean-docker   - Clean up the Docker environment"
	@echo "  test           - Open a tmux session with four panes"

# 生成证书
.PHONY: certs
certs:
	@read -p "Enter a username for the certificate (CN): " CN && \
	bash $(CERTS_DIR)/certs_generate.sh $$CN

# 运行客户端
client:
	@cd $(SRC_DIR) && python3 client.py

# 运行服务端
server:
	@cd $(SRC_DIR) && python3 server.py

# 检查镜像是否存在
check-docker-image:
	@if ! docker images | grep -q "$(DOCKER_IMAGE)"; then \
		echo "Pulling base image $(DOCKER_IMAGE)..."; \
		docker pull $(DOCKER_IMAGE); \
	fi

# Docker 环境搭建
setup-docker:
	# 创建 Docker 网络
	@if ! docker network ls | grep -q "$(DOCKER_NETWORK)"; then \
		docker network create $(DOCKER_NETWORK); \
	fi

	# 检查是否存在自定义镜像
	@if docker images | grep -q "$(CUSTOM_IMAGE)"; then \
		echo "Custom image $(CUSTOM_IMAGE) found. Using it to start containers."; \
	else \
		echo "Custom image $(CUSTOM_IMAGE) not found. Building from base image..."; \
		make check-docker-image; \
		docker run -dit --name $(TEMP_CONTAINER) $(DOCKER_IMAGE) bash; \
		docker exec $(TEMP_CONTAINER) mkdir -p /HUSTSSLChat; \
		docker cp . $(TEMP_CONTAINER):/HUSTSSLChat; \
		docker exec $(TEMP_CONTAINER) pip install -r /HUSTSSLChat/$(PYTHON_REQUIREMENTS); \
		docker commit $(TEMP_CONTAINER) $(CUSTOM_IMAGE); \
		docker rm -f $(TEMP_CONTAINER); \
		echo "Custom image $(CUSTOM_IMAGE) created."; \
	fi

	# 启动容器
	@for container in $(DOCKER_CONTAINERS); do \
		if ! docker ps -a | grep -q "$$container"; then \
			echo "Creating and starting container $$container..."; \
			docker run -dit --name $$container --network $(DOCKER_NETWORK) $(CUSTOM_IMAGE); \
		else \
			echo "Container $$container already exists. Skipping creation."; \
			docker start $$container > /dev/null; \
		fi \
	done

	@echo "Docker environment is ready. Connect to any host using:"
	@echo "  docker exec -it <host_name> bash"

# Docker 环境清理
clean-docker:
	# 停止并删除容器
	docker stop host1 host2 host3 $(TEMP_CONTAINER) || true
	docker rm host1 host2 host3 $(TEMP_CONTAINER) || true

	# 删除网络
	docker network rm $(DOCKER_NETWORK) || true

	# 删除自定义镜像
	docker rmi $(CUSTOM_IMAGE) || true

	@echo "Docker environment cleaned."

test: setup-docker
	@tmux new-session -d -s $(TMUX_SESSION) "docker exec -it host1 bash"
	@tmux split-window -h "docker exec -it host2 bash"
	@tmux split-window -v "docker exec -it host3 bash"
	@tmux select-pane -t 0
	@tmux split-window -v "bash"
	@tmux select-layout tiled
	@tmux attach -t $(TMUX_SESSION)