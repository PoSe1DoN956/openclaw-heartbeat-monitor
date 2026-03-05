#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地模型心跳驱动 OpenClaw 自动执行服务
"""

import os
import json
import time
import logging
import schedule
import requests
import subprocess
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('heartbeat.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('heartbeat_service')

class HeartbeatService:
    def __init__(self, config_file="config.json"):
        # 从配置文件读取配置
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.ollama_url = config.get("ollama_url", "http://localhost:11434/api/generate")
            self.model = config.get("model", "qwen3:8B")
            self.check_interval = config.get("check_interval", 5)  # 5分钟
            self.whitelist_commands = config.get("whitelist_commands", ["system_check", "postgres_backup", "log_cleanup", "service_keepalive"])
            self.openclaw_path = config.get("openclaw_path", "openclaw")  # 假设openclaw在PATH中
            
            # 配置日志
            log_file = config.get("log_file", "heartbeat.log")
            log_level = getattr(logging, config.get("log_level", "INFO"))
            
            # 重新配置日志
            for handler in logger.handlers:
                logger.removeHandler(handler)
            
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
            
            logger.info(f"成功加载配置文件: {config_file}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            # 使用默认配置
            self.ollama_url = "http://localhost:11434/api/generate"
            self.model = "qwen3:8B"
            self.check_interval = 5  # 5分钟
            self.whitelist_commands = ["system_check", "postgres_backup", "log_cleanup", "service_keepalive"]
            self.openclaw_path = "openclaw"
        
    def get_current_time(self):
        """获取当前时间"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def request_ollama(self):
        """请求本地 Ollama 接口进行轻量推理"""
        try:
            prompt = "请返回一个JSON格式的对象，包含以下字段：\n"
            prompt += "- action: 字符串，可选值为 system_check、postgres_backup、log_cleanup、service_keepalive 或 none\n"
            prompt += "- reason: 字符串，说明执行该操作的原因\n"
            prompt += "\n示例输出：\n"
            prompt += '{"action": "system_check", "reason": "定期系统检查"}'
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "format": "json",
                "stream": False
            }
            
            logger.info(f"[{self.get_current_time()}] 向 Ollama 发送心跳请求...")
            response = requests.post(self.ollama_url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if "response" in result:
                return json.loads(result["response"])
            else:
                logger.error(f"Ollama 响应格式错误: {result}")
                return {"action": "none", "reason": "响应格式错误"}
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误: {e}")
            return {"action": "none", "reason": "JSON解析失败"}
        except requests.RequestException as e:
            logger.error(f"请求 Ollama 失败: {e}")
            return {"action": "none", "reason": "请求失败"}
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return {"action": "none", "reason": "未知错误"}
    
    def execute_openclaw(self, command):
        """执行 OpenClaw 命令"""
        try:
            logger.info(f"执行 OpenClaw 命令: {command}")
            result = subprocess.run(
                [self.openclaw_path, command],
                capture_output=True,
                text=True,
                timeout=60
            )
            logger.info(f"命令执行结果: {result.stdout}")
            if result.stderr:
                logger.error(f"命令执行错误: {result.stderr}")
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error(f"命令执行超时: {command}")
            return False
        except Exception as e:
            logger.error(f"执行命令时出错: {e}")
            return False
    
    def process_heartbeat(self):
        """处理心跳检测和任务调度"""
        try:
            logger.info(f"[{self.get_current_time()}] 开始心跳检测...")
            
            # 请求 Ollama
            response = self.request_ollama()
            logger.info(f"模型返回: {json.dumps(response)}")
            
            # 解析响应
            action = response.get("action", "none")
            reason = response.get("reason", "无")
            
            # 白名单校验
            if action in self.whitelist_commands:
                logger.info(f"执行合法指令: {action}，原因: {reason}")
                success = self.execute_openclaw(action)
                if success:
                    logger.info(f"指令执行成功: {action}")
                else:
                    logger.error(f"指令执行失败: {action}")
            elif action == "none":
                logger.info(f"无需执行操作，原因: {reason}")
            else:
                logger.warning(f"指令不在白名单中: {action}")
                
        except Exception as e:
            logger.error(f"处理心跳时出错: {e}")
    
    def run(self):
        """启动服务"""
        logger.info("心跳服务启动")
        
        # 立即执行一次
        self.process_heartbeat()
        
        # 定时执行
        schedule.every(self.check_interval).minutes.do(self.process_heartbeat)
        
        # 主循环
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("服务被手动停止")
        except Exception as e:
            logger.error(f"服务运行出错: {e}")

if __name__ == "__main__":
    service = HeartbeatService()
    service.run()