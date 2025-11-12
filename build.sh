#!/bin/bash

IMAGE_NAME="weijiangwu/crawler-service"
VERSION="1.0.0"

# 使用环境变量登录 Docker Hub
# 使用前请设置: export DOCKER_TOKEN=your_token_here
echo "Logging into Docker Hub"
if [ -z "$DOCKER_TOKEN" ]; then
    echo "Error: DOCKER_TOKEN environment variable is not set"
    echo "Please run: export DOCKER_TOKEN=your_docker_token"
    exit 1
fi
echo "$DOCKER_TOKEN" | docker login -u weijiangwu --password-stdin

# 构建镜像
echo "Building image"
docker buildx build --platform linux/amd64,linux/arm64 -t $IMAGE_NAME:$VERSION --load .

# 将新构建的镜像标记为 latest
docker tag $IMAGE_NAME:$VERSION $IMAGE_NAME:latest

# 推送新版本的镜像到 Docker Hub
echo "Pushing new version image to Docker Hub"
docker push $IMAGE_NAME:$VERSION

# 推送 latest 镜像到 Docker Hub
echo "Pushing latest image to Docker Hub"
docker push $IMAGE_NAME:latest

echo "Push done: $IMAGE_NAME:$VERSION"

