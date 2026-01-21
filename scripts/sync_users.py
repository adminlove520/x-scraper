#!/usr/bin/env python3
import os
import json
import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
base_dir = Path(__file__).parent.parent
sys.path.append(str(base_dir))

from app.services.user_service import UserService
from app.core.config import Config
from app.core.logger import logger

def sync_users(fetch_metadata=False):
    users_txt_path = Config.CONFIG_DIR / "users.txt"
    users_json_path = Config.CONFIG_DIR / "users.json"

    if not users_txt_path.exists():
        logger.error(f"找不到 {users_txt_path}")
        return

    # 1. 读取 users.txt
    with open(users_txt_path, 'r', encoding='utf-8') as f:
        txt_usernames = set()
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # 兼容 @ 符号
                txt_usernames.add(line.lstrip('@').lower())

    # 2. 读取现有的 users.json
    existing_users = []
    if users_json_path.exists():
        try:
            with open(users_json_path, 'r', encoding='utf-8') as f:
                existing_users = json.load(f)
        except Exception as e:
            logger.error(f"读取 users.json 失败: {e}")

    # 将现有用户转为字典，方便查找
    existing_users_dict = {u['username'].lower(): u for u in existing_users}

    # 3. 同步
    new_users_list = []
    user_service = UserService()

    for username in sorted(txt_usernames):
        if username in existing_users_dict:
            # 保留现有配置
            new_users_list.append(existing_users_dict[username])
        else:
            # 新用户：如果开启了 fetch 则获取元数据，否则使用极简默认值
            logger.info(f"发现新用户: @{username}")
            if fetch_metadata:
                metadata = user_service.get_user_metadata(username)
                new_users_list.append(metadata)
            else:
                new_users_list.append({
                    "username": username,
                    "count": 500,
                    "priority": "low",
                    "tags": []
                })

    # 4. 保存
    with open(users_json_path, 'w', encoding='utf-8') as f:
        json.dump(new_users_list, f, indent=2, ensure_ascii=False)
    
    logger.info(f"同步完成！当前共有 {len(new_users_list)} 个活跃订阅用户。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="同步 users.txt 到 users.json")
    parser.add_argument("--fetch", action="store_true", help="是否通过 Twitter API 获取新用户的元数据")
    args = parser.parse_args()

    sync_users(fetch_metadata=args.fetch)
