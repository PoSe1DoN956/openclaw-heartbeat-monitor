# 本地模型心跳驱动 OpenClaw 自动执行服务

## 项目简介

本项目是一个基于 Python 开发的本地模型心跳服务，用于定时请求本地 Ollama 接口进行轻量推理，并根据模型输出自动调用 OpenClaw 执行指定任务。

## 功能特性

- **定时心跳服务**：每隔 5 分钟主动请求本地 Ollama 接口，做一次轻量推理
- **模型输出约束**：只返回固定格式 JSON，用于判断是否触发任务
- **指令调度**：解析模型输出，白名单校验，合法指令自动调用 OpenClaw 执行
- **任务池**：系统状态巡检、PostgreSQL 备份、日志清理、服务保活
- **日志与异常**：完整运行日志、JSON 解析容错、重试机制
- **部署友好**：提供一键启动脚本、后台运行方案、开机自启配置

## 技术栈

- Python 3.7+
- requests
- schedule
- Ollama API
- subprocess 调用 OpenClaw

## 快速开始

### 1. 环境准备

1. 安装 Python 3.7 或更高版本
2. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```
3. 确保本地已安装并运行 Ollama（qwen3:8B 模型）
4. 确保 OpenClaw 已安装并添加到系统 PATH 中

### 2. 配置修改

根据实际情况修改 `config.json` 文件：

```json
{
  "ollama_url": "http://localhost:11434/api/generate",
  "model": "qwen3:8B",
  "check_interval": 5,
  "whitelist_commands": ["system_check", "postgres_backup", "log_cleanup", "service_keepalive"],
  "openclaw_path": "openclaw",
  "log_file": "heartbeat.log",
  "log_level": "INFO"
}
```

### 3. 启动服务

#### Windows 环境

- **前台运行**：双击 `start_service.bat` 文件
- **后台运行**：双击 `run_service.vbs` 文件

#### WSL2 环境

```bash
chmod +x start_service.sh
./start_service.sh
```

## 开机自启配置

### Windows 环境

1. 按下 `Win + R` 打开运行对话框
2. 输入 `shell:startup` 并回车
3. 将 `run_service.vbs` 文件复制到启动文件夹中

### WSL2 环境

1. 编辑 crontab：
   ```bash
   crontab -e
   ```
2. 添加以下内容（根据实际路径修改）：
   ```
   @reboot /path/to/start_service.sh
   ```

## 日志管理

- 运行日志保存在 `heartbeat.log` 文件中
- 可通过修改 `config.json` 中的 `log_file` 和 `log_level` 调整日志设置

## 任务说明

- **system_check**：系统状态巡检
- **postgres_backup**：PostgreSQL 数据库备份
- **log_cleanup**：日志清理
- **service_keepalive**：服务保活

## 注意事项

1. 确保 Ollama 服务正在运行
2. 确保 OpenClaw 已正确安装并配置
3. 首次运行时，可能需要等待 Ollama 加载模型
4. 如遇网络或服务异常，系统会自动重试

## 故障排查

- 检查 `heartbeat.log` 日志文件
- 确保 Ollama API 地址正确
- 确保 OpenClaw 命令可正常执行
- 检查网络连接是否正常