import logging
import os
from config import Config

def setup_logger():
    logger = logging.getLogger('crossborder_agent')
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))

    # 日志目录按 LOG_FILE 的实际位置创建（支持绝对路径，不依赖当前工作目录）
    log_dir = os.path.dirname(os.path.abspath(Config.LOG_FILE)) or '.'
    os.makedirs(log_dir, exist_ok=True)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler = logging.FileHandler(Config.LOG_FILE)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_error(component, message):
    logger = logging.getLogger('crossborder_agent')
    logger.error(f'Error in {component}: {message}')

def log_api_call(endpoint, url, request_data, response_data, status, latency):
    logger = logging.getLogger('crossborder_agent')
    logger.info(f'API Call: {endpoint} - {url} - Status: {status} - Latency: {latency}ms')

logger = setup_logger()
