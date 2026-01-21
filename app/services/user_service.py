import re
from typing import List, Dict, Optional
from app.crawlers.x_crawler import XCrawler
from app.core.logger import logger

class UserService:
    def __init__(self, crawler: Optional[XCrawler] = None):
        self.crawler = crawler or XCrawler()

    def get_user_metadata(self, username: str) -> Dict:
        """
        获取用户元数据并自动生成配置信息
        """
        username = username.lstrip('@')
        user_info = self.crawler.get_user_by_username(username)
        
        if not user_info:
            logger.warning(f"无法获取用户 @{username} 的信息，将使用默认配置")
            return {
                "username": username,
                "count": 500,
                "priority": "low",
                "tags": []
            }

        # 1. 自动设置优先级 (根据粉丝数)
        followers_count = user_info.get("public_metrics", {}).get("followers_count", 0)
        if followers_count > 100000:
            priority = "high"
        elif followers_count > 10000:
            priority = "medium"
        else:
            priority = "low"

        # 2. 自动提取标签 (从简介中提取话题标签)
        description = user_info.get("description", "")
        tags = self._extract_tags(description)

        metadata = {
            "username": username,
            "count": 1000 if priority == "high" else 500,
            "priority": priority,
            "tags": tags,
            "name": user_info.get("name"),
            "id": user_info.get("id")
        }
        
        return metadata

    def _extract_tags(self, description: str) -> List[str]:
        """从用户简介中提取 #话题 或关键词"""
        if not description:
            return []
        
        # 提取 # 标签
        hashtags = re.findall(r'#(\w+)', description)
        
        # 常见关键词提取 (可选扩展)
        keywords = []
        common_areas = ["crypto", "ai", "web3", "tech", "nft", "btc", "eth", "solana", "trading"]
        for area in common_areas:
            if area.lower() in description.lower() and area not in hashtags:
                keywords.append(area)
        
        return list(set(hashtags + keywords))
