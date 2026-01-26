import os
import json
import logging
import re
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量，支持从项目根目录加载.env文件
dotenv_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 验证环境变量加载
logger.info(f".env文件路径: {dotenv_path}")
logger.info(f".env文件存在: {dotenv_path.exists()}")

class Config:
    # 基础路径
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    CONFIG_DIR = BASE_DIR / "config"
    
    # 确保目录存在
    DATA_DIR.mkdir(exist_ok=True)
    CONFIG_DIR.mkdir(exist_ok=True)
    
    # Twitter API 配置
    # 1. 支持 Bearer Token 认证
    _raw_tokens = os.getenv("TWITTER_BEARER_TOKEN", "")
    logger.info(f"原始TWITTER_BEARER_TOKEN: {_raw_tokens}")
    
    # 改进Token解析逻辑，确保正确处理各种分隔符
    TWITTER_BEARER_TOKEN = []
    if _raw_tokens:
        # 支持多种分隔符：英文逗号、中文全角逗号、空格、换行
        tokens = re.split(r'[,，\s\n]+', _raw_tokens)
        TWITTER_BEARER_TOKEN = [t.strip() for t in tokens if t.strip()]
        logger.info(f"解析后的Bearer Token数量: {len(TWITTER_BEARER_TOKEN)}")
        logger.info(f"解析后的Bearer Token列表: {TWITTER_BEARER_TOKEN}")
    else:
        logger.warning("未检测到TWITTER_BEARER_TOKEN环境变量")
    
    # 2. 支持 API Key/Secret 认证
    TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
    TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
    logger.info(f"TWITTER_API_KEY存在: {bool(TWITTER_API_KEY)}")
    logger.info(f"TWITTER_API_SECRET存在: {bool(TWITTER_API_SECRET)}")
    
    # 3. 认证方式检查
    if not TWITTER_BEARER_TOKEN and not (TWITTER_API_KEY and TWITTER_API_SECRET):
        logger.error("未检测到有效的Twitter API认证信息，请配置TWITTER_BEARER_TOKEN或TWITTER_API_KEY+TWITTER_API_SECRET")
    
    # 其他环境变量
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
    DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID") # 推送频道 ID
    DISCORD_ADMIN_ID = os.getenv("DISCORD_ADMIN_ID") # 管理员 ID
    
    # 日志输出环境变量状态
    logger.info(f"DISCORD_TOKEN存在: {bool(DISCORD_TOKEN)}")
    logger.info(f"DISCORD_WEBHOOK_URL存在: {bool(DISCORD_WEBHOOK_URL)}")
    logger.info(f"DISCORD_CHANNEL_ID存在: {bool(DISCORD_CHANNEL_ID)}")
    logger.info(f"DISCORD_ADMIN_ID存在: {bool(DISCORD_ADMIN_ID)}")
    
    # 全局采集用户列表
    GLOBAL_USERS_FILE = CONFIG_DIR / "users.json"
    
    # 已处理推文 ID 记录
    PROCESSED_IDS_FILE = DATA_DIR / "processed_ids.json"
    
    # 关注列表快照记录
    FOLLOWING_SNAPSHOT_FILE = DATA_DIR / "following_snapshot.json"
    
    # 队列系统配置
    QUEUE_CONFIG = {
        "twitter_api": {
            "max_tokens": 15,  # 15 requests / 15 minutes
            "refill_interval": 900  # 15 minutes in seconds
        },
        "discord_bot": {
            "max_tokens": 5,     # 5 messages / second
            "refill_interval": 1  # 1 second
        },
        "webhook_push": {
            "max_tokens": 3,      # 3 webhooks / second
            "refill_interval": 1   # 1 second
        }
    }

    @classmethod
    def get_global_users(cls):
        """获取全局订阅用户列表"""
        if not cls.GLOBAL_USERS_FILE.exists():
            return []
        try:
            with open(cls.GLOBAL_USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"无法读取全局用户配置文件: {e}")
            return []

    @classmethod
    def get_dc_user_configs(cls):
        """获取所有 Discord 用户的订阅配置"""
        configs = []
        for file in cls.DATA_DIR.glob("users_dc_*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    configs.append({
                        "id": file.stem.replace("users_dc_", ""),
                        "users": json.load(f)
                    })
            except Exception as e:
                logging.error(f"无法读取用户配置 {file.name}: {e}")
        return configs

    @classmethod
    def save_dc_user_config(cls, user_id, users):
        """保存特定 Discord 用户的订阅配置"""
        file_path = cls.DATA_DIR / f"users_dc_{user_id}.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"无法保存用户配置 {user_id}: {e}")
            return False

    @classmethod
    def load_processed_ids(cls):
        """加载已处理的推文 ID"""
        if not cls.PROCESSED_IDS_FILE.exists():
            return set()
        try:
            with open(cls.PROCESSED_IDS_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception as e:
            logging.error(f"无法读取已处理 ID 文件: {e}")
            return set()

    @classmethod
    def save_processed_ids(cls, processed_ids):
        """保存已处理的推文 ID"""
        try:
            with open(cls.PROCESSED_IDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(list(processed_ids), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"无法保存已处理 ID 文件: {e}")

    @classmethod
    def load_following_snapshots(cls):
        """加载关注列表快照"""
        if not cls.FOLLOWING_SNAPSHOT_FILE.exists():
            return {}
        try:
            with open(cls.FOLLOWING_SNAPSHOT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"无法读取关注快照文件: {e}")
            return {}

    @classmethod
    def save_following_snapshots(cls, snapshots):
        """保存关注列表快照"""
        try:
            with open(cls.FOLLOWING_SNAPSHOT_FILE, 'w', encoding='utf-8') as f:
                json.dump(snapshots, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"无法保存关注快照文件: {e}")
