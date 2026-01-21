import os
import requests
import time
from typing import List, Dict, Optional
from app.core.config import Config
from app.core.logger import logger

class XCrawler:
    def __init__(self, bearer_tokens: List[str] = None):
        self.tokens = bearer_tokens or Config.TWITTER_BEARER_TOKEN
        self.token_index = 0
        self.base_url = "https://api.twitter.com/2"
        # 代理配置
        self.proxies = self._get_proxies()
        self._update_headers()

    def _get_proxies(self):
        """从环境变量获取代理配置"""
        proxies = {}
        http_proxy = (os.getenv("HTTP_PROXY") or os.getenv("http_proxy", "")).strip()
        https_proxy = (os.getenv("HTTPS_PROXY") or os.getenv("https_proxy", "")).strip()
        if http_proxy:
            proxies["http"] = http_proxy
        if https_proxy:
            proxies["https"] = https_proxy
        return proxies

    def _update_headers(self):
        """更新当前使用的 Token 请求头"""
        if not self.tokens or not self.tokens[0]:
            logger.error("未配置 TWITTER_BEARER_TOKEN")
            self.headers = {}
            return

        current_token = self.tokens[self.token_index].strip()
        self.headers = {
            "Authorization": f"Bearer {current_token}",
            "User-Agent": "v2UserTweetsPython"
        }
        logger.debug(f"当前使用 Token 索引: {self.token_index}")

    def _rotate_token(self):
        """轮换到下一个 Token"""
        if len(self.tokens) > 1:
            self.token_index = (self.token_index + 1) % len(self.tokens)
            self._update_headers()
            logger.info(f"已轮换到下一个 Twitter Token (索引: {self.token_index})")

    def _get_request(self, url: str, params: Dict = None, retry_count: int = 0):
        """通用请求处理，包含速率限制检查和 Token 轮换"""
        if not self.headers:
            return None

        try:
            response = requests.get(url, headers=self.headers, params=params, proxies=self.proxies, timeout=10)
            
            # 处理速率限制
            if response.status_code == 429:
                if retry_count < len(self.tokens):
                    logger.warning(f"Token {self.token_index} 触发速率限制，正在尝试轮换...")
                    self._rotate_token()
                    return self._get_request(url, params, retry_count + 1)
                else:
                    wait_time = 15 * 60
                    logger.warning(f"所有 Token 均已达到限制，等待 15 分钟...")
                    time.sleep(wait_time)
                    return self._get_request(url, params, 0)

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API 请求失败 (Token Index {self.token_index}): {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """通过用户名获取用户信息"""
        username = username.lstrip('@')
        url = f"{self.base_url}/users/by/username/{username}"
        params = {
            "user.fields": "public_metrics,description,name,profile_image_url"
        }
        data = self._get_request(url, params)
        if data and "data" in data:
            return data["data"]
        return None

    def get_following(self, user_id: str, max_results: int = 100) -> List[Dict]:
        """获取用户关注的列表"""
        url = f"{self.base_url}/users/{user_id}/following"
        params = {
            "max_results": max_results,
            "user.fields": "public_metrics,description,name"
        }
        data = self._get_request(url, params)
        if data and "data" in data:
            return data["data"]
        return []

    def get_latest_tweets(self, user_id: str, count: int = 5) -> List[Dict]:
        """获取用户最新的推文"""
        url = f"{self.base_url}/users/{user_id}/tweets"
        params = {
            "max_results": min(100, max(5, count)),
            "tweet.fields": "created_at,public_metrics,entities",
            "exclude": "retweets,replies"
        }
        data = self._get_request(url, params)
        if data and "data" in data:
            return data["data"]
        return []

    def get_top_users(self, usernames: List[str], top_n: int = 10) -> List[Dict]:
        """获取前 N 名关注者最多的用户信息"""
        users_info = []
        for username in usernames:
            user = self.get_user_by_username(username)
            if user:
                users_info.append(user)
            time.sleep(1)
        
        sorted_users = sorted(
            users_info, 
            key=lambda x: x.get("public_metrics", {}).get("followers_count", 0), 
            reverse=True
        )
        return sorted_users[:top_n]
