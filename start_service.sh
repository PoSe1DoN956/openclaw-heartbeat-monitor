#!/bin/bash
cd "$(dirname "$0")"
echo "启动本地模型心跳服务..."
python3 heartbeat_service.py