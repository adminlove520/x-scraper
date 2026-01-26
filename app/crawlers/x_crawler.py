import os
import time
import asyncio
import aiohttp
import hmac
import hashlib
import base64
import random
import string
from typing import List, Dict, Optional
from app.core.config import Config
from app.core.logger import logger
from app.core.queue_manager import queue_manager

class XCrawler:
    def __init__(self, bearer_tokens: List[str] = None):
        # 1. 支持 Bearer Token 认证
        self.bearer_tokens = bearer_tokens or Config.TWITTER_BEARER_TOKEN
        
        # 2. 支持 API Key/Secret 认证
        self.api_key = Config.TWITTER_API_KEY
        self.api_secret = Config.TWITTER_API_SECRET
        
        # 认证方式
        self.auth_type = "bearer" if self.bearer_tokens else ("oauth1" if self.api_key and self.api_secret else None)
        
        self.token_index = 0
        self.base_url = "https://api.twitter.com/2"
        # 代理配置
        self.proxies = self._get_proxies()
        self._update_headers()
        # 会话对象
        self.session = None

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

    def _generate_nonce(self):
        """生成随机字符串用于OAuth 1.0a"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

    def _generate_oauth_signature(self, url, params, method="GET"):
        """生成OAuth 1.0a签名"""
        # 准备签名基础字符串
        oauth_params = {
            "oauth_consumer_key": self.api_key,
            "oauth_nonce": self._generate_nonce(),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_version": "1.0"
        }
        
        # 合并所有参数
        all_params = {**oauth_params, **params}
        
        # 排序参数
        sorted_params = sorted(all_params.items())
        
        # 构建参数字符串
        param_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # 构建基础字符串
        base_string = f"{method}&{base64.b64encode(url.encode()).decode()}&{base64.b64encode(param_string.encode()).decode()}"
        
        # 构建签名密钥
        signing_key = f"{self.api_secret}&"
        
        # 生成签名
        signature = hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        oauth_params["oauth_signature"] = base64.b64encode(signature).decode()
        
        return oauth_params

    def _build_oauth_header(self, url, params, method="GET"):
        """构建OAuth 1.0a请求头"""
        oauth_params = self._generate_oauth_signature(url, params, method)
        oauth_header = "OAuth " + ", ".join([f"{k}=\"{v}\"" for k, v in oauth_params.items()])
        return oauth_header

    def _update_headers(self):
        """更新当前使用的认证请求头"""
        self.headers = {
            "User-Agent": "v2UserTweetsPython"
        }
        
        if self.auth_type == "bearer":
            if not self.bearer_tokens or not self.bearer_tokens[0]:
                logger.error("未配置有效的 TWITTER_BEARER_TOKEN")
                return
            
            current_token = self.bearer_tokens[self.token_index].strip()
            self.headers["Authorization"] = f"Bearer {current_token}"
            logger.debug(f"当前使用 Bearer Token 索引: {self.token_index}")
        elif self.auth_type == "oauth1":
            # OAuth 1.0a 认证的头信息在每次请求时动态生成
            logger.debug("使用 OAuth 1.0a 认证")
        else:
            logger.error("未配置有效的 Twitter API 认证信息")

    def _rotate_token(self):
        """轮换到下一个 Token"""
        if self.auth_type == "bearer" and len(self.bearer_tokens) > 1:
            self.token_index = (self.token_index + 1) % len(self.bearer_tokens)
            self._update_headers()
            logger.info(f"已轮换到下一个 Twitter Bearer Token (索引: {self.token_index})")

    async def _get_request(self, url: str, params: Dict = None, retry_count: int = 0):
        """通用异步请求处理，包含速率限制检查和 Token 轮换"""
        if not self.auth_type:
            logger.error("未配置有效的认证方式")
            return None

        try:
            if self.session is None:
                self.session = aiohttp.ClientSession()
            
            # 准备请求头
            request_headers = self.headers.copy()
            
            # 根据认证类型处理请求头
            if self.auth_type == "oauth1":
                # 为每个请求构建 OAuth 1.0a 头
                oauth_header = self._build_oauth_header(url, params or {})
                request_headers["Authorization"] = oauth_header
            
            async with self.session.get(url, headers=request_headers, params=params, proxy=self.proxies.get("https"), timeout=10) as response:
                # 处理速率限制
                if response.status == 429:
                    if self.auth_type == "bearer" and retry_count < len(self.bearer_tokens):
                        logger.warning(f"Token {self.token_index} 触发速率限制，正在尝试轮换...")
                        self._rotate_token()
                        return await self._get_request(url, params, retry_count + 1)
                    else:
                        wait_time = 15 * 60
                        logger.warning(f"所有认证方式均已达到限制，等待 15 分钟...")
                        await asyncio.sleep(wait_time)
                        return await self._get_request(url, params, 0)

                response.raise_for_status()
                return await response.json()
        except Exception as e:
            token_info = f" (Token Index {self.token_index})" if self.auth_type == "bearer" else " (OAuth 1.0a)"
            logger.error(f"API 请求失败{token_info}: {e}")
            return None

    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """通过用户名获取用户信息"""
        username = username.lstrip('@')
        url = f"{self.base_url}/users/by/username/{username}"
        params = {
            "user.fields": "public_metrics,description,name,profile_image_url"
        }
        data = await self._get_request(url, params)
        if data and "data" in data:
            return data["data"]
        return None

    async def get_following(self, user_id: str, max_results: int = 100) -> List[Dict]:
        """获取用户关注的列表"""
        url = f"{self.base_url}/users/{user_id}/following"
        params = {
            "max_results": max_results,
            "user.fields": "public_metrics,description,name"
        }
        data = await self._get_request(url, params)
        if data and "data" in data:
            return data["data"]
        return []

    async def get_latest_tweets(self, user_id: str, count: int = 5) -> List[Dict]:
        """获取用户最新的推文"""
        url = f"{self.base_url}/users/{user_id}/tweets"
        params = {
            "max_results": min(100, max(5, count)),
            "tweet.fields": "created_at,public_metrics,entities",
            "exclude": "retweets,replies"
        }
        data = await self._get_request(url, params)
        if data and "data" in data:
            return data["data"]
        return []

    async def get_top_users(self, usernames: List[str], top_n: int = 10) -> List[Dict]:
        """获取前 N 名关注者最多的用户信息"""
        users_info = []
        for username in usernames:
            user = await self.get_user_by_username(username)
            if user:
                users_info.append(user)
            await asyncio.sleep(1)
        
        sorted_users = sorted(
            users_info, 
            key=lambda x: x.get("public_metrics", {}).get("followers_count", 0), 
            reverse=True
        )
        return sorted_users[:top_n]

    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            self.session = None
