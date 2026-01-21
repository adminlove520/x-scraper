import logging
import sys
from pathlib import Path

def setup_logger(name="x_scraper", log_file="app.log", level=logging.INFO):
    """设置全局日志格式"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 输出到终端
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 输出到文件
    log_path = Path(__file__).parent.parent.parent / "data" / log_file
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# 初始化默认日志
logger = setup_logger()
