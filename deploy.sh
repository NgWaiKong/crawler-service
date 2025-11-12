#!/bin/bash
IMAGE_NAME="weijiangwu/crawler-service"

# 拉取最新镜像
echo "Pulling latest images..."
docker pull $IMAGE_NAME:latest

# 停止并移除现有容器
echo "Stopping and removing existing containers..."
docker compose down

# 启动新的容器
echo "Starting new containers..."
docker compose up -d

# 显示容器状态
echo "Container status:"
docker compose ps

echo "Docker Compose deployment completed!"