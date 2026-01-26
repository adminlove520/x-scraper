import asyncio
import json
import aiohttp
from app.core.logger import logger
from app.core.config import Config
from app.core.queue_manager import queue_manager

class WebhookPusher:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or Config.DISCORD_WEBHOOK_URL
        self.session = None

    async def _push_async(self, content: str = None, embeds: list = None):
        """异步推送消息到 Discord Webhook"""
        if not self.webhook_url:
            logger.error("未配置 Discord Webhook URL")
            return False
        
        payload = {}
        if content:
            payload["content"] = content
        if embeds:
            payload["embeds"] = embeds

        try:
            if self.session is None:
                self.session = aiohttp.ClientSession()
            
            async with self.session.post(
                self.webhook_url, 
                data=json.dumps(payload), 
                headers={"Content-Type": "application/json"}, 
                timeout=10
            ) as response:
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Webhook 推送失败: {e}")
            return False

    async def push(self, content: str = None, embeds: list = None):
        """推送消息到 Discord Webhook，通过队列管理器"""
        # 将推送任务添加到队列
        await queue_manager.add_task(
            "webhook_push",
            self._push_async,
            content, embeds
        )
        return True

    def push_sync(self, content: str = None, embeds: list = None):
        """同步推送接口，内部转为异步"""
        return asyncio.run(self.push(content, embeds))

    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            self.session = None

    @staticmethod
    def format_tweet_embed(tweet: dict, user_info: dict):
        """格式化推文为 Discord Embed"""
        username = user_info.get("username", "Unknown")
        name = user_info.get("name", "Unknown")
        
        embed = {
            "title": f"来自 {name} (@{username}) 的新推文",
            "description": tweet.get("text", ""),
            "url": f"https://x.com/{username}/status/{tweet.get('id')}",
            "color": 0x1DA1F2, # Twitter Blue
            "fields": [
                {
                    "name": "互动",
                    "value": f"💬 {tweet.get('public_metrics', {}).get('reply_count', 0)} | 🔁 {tweet.get('public_metrics', {}).get('retweet_count', 0)} | ❤️ {tweet.get('public_metrics', {}).get('like_count', 0)}",
                    "inline": True
                }
            ],
            "footer": {
                "text": f"发布于: {tweet.get('created_at')}"
            }
        }
        return embed
