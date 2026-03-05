@echo off
cd /d "%~dp0"
echo 启动本地模型心跳服务...
python heartbeat_service.py
pause