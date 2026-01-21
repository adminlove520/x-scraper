import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # 基础路径
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    CONFIG_DIR = BASE_DIR / "config"
    
    # 确保目录存在
    DATA_DIR.mkdir(exist_ok=True)
    
    # Twitter API 配置
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "").split(",") # 支持多个 Token 轮换
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
    DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID") # 推送频道 ID
    DISCORD_ADMIN_ID = os.getenv("DISCORD_ADMIN_ID") # 管理员 ID
    
    # 全局采集用户列表
    GLOBAL_USERS_FILE = CONFIG_DIR / "users.json"
    
    # 已处理推文 ID 记录
    PROCESSED_IDS_FILE = DATA_DIR / "processed_ids.json"
    
    # 关注列表快照记录
    FOLLOWING_SNAPSHOT_FILE = DATA_DIR / "following_snapshot.json"

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
