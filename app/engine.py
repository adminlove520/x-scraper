import asyncio
import time
import os
from datetime import datetime
import discord
from app.core.config import Config
from app.core.logger import logger
from app.crawlers.x_crawler import XCrawler
from app.pushers.webhook_pusher import WebhookPusher
from app.pushers.discord_bot import bot
from app.core.queue_manager import queue_manager

class ScraperEngine:
    def __init__(self):
        self.crawler = XCrawler()
        self.webhook_pusher = WebhookPusher()
        self.processed_ids = Config.load_processed_ids()
        self.following_snapshots = Config.load_following_snapshots()

    async def run_periodic_check(self, interval_seconds: int = 300):
        """定期检查所有订阅的用户"""
        while True:
            logger.info("开始一轮全面检查...")
            try:
                # 1. 处理全局订阅 (Webhook)
                await self.check_global_subscriptions()
                
                # 2. 处理 Discord 用户专用订阅 (Bot + Mention)
                await self.check_dc_user_subscriptions()
                
                # 保存状态
                Config.save_processed_ids(self.processed_ids)
                Config.save_following_snapshots(self.following_snapshots)
                
            except Exception as e:
                logger.error(f"检查周期发生错误: {e}")
            
            logger.info(f"一轮检查结束，等待 {interval_seconds} 秒...")
            await asyncio.sleep(interval_seconds)

    async def check_global_subscriptions(self):
        """检查 config/users.json 中的全局订阅"""
        users = Config.get_global_users()
        if not users:
            return

        for user_entry in users:
            username = user_entry.get("username")
            user_info = await self.crawler.get_user_by_username(username)
            if not user_info:
                continue
            
            # 这里的全局订阅目前只做推文监控
            await self._check_tweets(user_info, is_global=True)
            # 全局订阅也可以选择性监控关注列表，目前保持简洁只监控个人
            
            await asyncio.sleep(2)

    async def check_dc_user_subscriptions(self):
        """检查 data/users_dc_*.json 中的个人订阅"""
        dc_configs = Config.get_dc_user_configs()
        if not dc_configs:
            return

        for config in dc_configs:
            discord_user_id = config["id"]
            users = config["users"]
            
            for user_entry in users:
                username = user_entry.get("username")
                user_info = await self.crawler.get_user_by_username(username)
                if not user_info:
                    continue
                
                # 1. 监控推文
                await self._check_tweets(user_info, discord_user_id=discord_user_id)
                
                # 2. 监控关注列表
                await self._check_following(user_info, discord_user_id=discord_user_id)
                
                await asyncio.sleep(2)

    async def _check_tweets(self, user_info: dict, discord_user_id: str = None, is_global: bool = False):
        """辅助函数：检查并推送推文"""
        username = user_info["username"]
        tweets = await self.crawler.get_latest_tweets(user_info["id"])
        
        for tweet in tweets:
            if tweet["id"] not in self.processed_ids:
                logger.info(f"发现新推文: {username} - {tweet['id']}")
                
                if is_global:
                    embed = WebhookPusher.format_tweet_embed(tweet, user_info)
                    await self.webhook_pusher.push(embeds=[embed])
                
                if discord_user_id:
                    await self.push_to_discord_user(discord_user_id, tweet, user_info, type="tweet")
                
                self.processed_ids.add(tweet["id"])

    async def _check_following(self, user_info: dict, discord_user_id: str):
        """辅助函数：检查并推送新关注"""
        user_id = user_info["id"]
        username = user_info["username"]
        
        current_following = await self.crawler.get_following(user_id)
        if not current_following:
            return

        current_following_ids = {u["id"] for u in current_following}
        
        # 获取上次的快照
        last_snapshot = self.following_snapshots.get(user_id, [])
        if last_snapshot:
            last_following_ids = set(last_snapshot)
            # 找出新关注的人
            new_following_ids = current_following_ids - last_following_ids
            
            for new_id in new_following_ids:
                new_user_info = next((u for u in current_following if u["id"] == new_id), None)
                if new_user_info:
                    logger.info(f"发现新关注: @{username} 关注了 @{new_user_info['username']}")
                    await self.push_to_discord_user(discord_user_id, new_user_info, user_info, type="following")
        
        # 更新快照
        self.following_snapshots[user_id] = list(current_following_ids)

    async def _send_discord_message(self, channel_id: int, content: str, embed: discord.Embed):
        """异步发送Discord消息"""
        channel = bot.get_channel(channel_id)
        if not channel:
            return
        await channel.send(content=content, embed=embed)

    async def push_to_discord_user(self, discord_user_id: str, data: dict, target_user_info: dict, type: str = "tweet"):
        """通过 Bot 推送给特定用户并 @他，通过队列管理器"""
        target_channel_id = int(os.getenv("DISCORD_CHANNEL_ID", 0))
        if not target_channel_id:
            return

        target_username = target_user_info["username"]
        
        if type == "tweet":
            embed = discord.Embed(
                title=f"🔔 新推文提醒：{target_user_info['name']} (@{target_username})",
                description=data.get("text", ""),
                url=f"https://x.com/{target_username}/status/{data.get('id')}",
                color=0x1DA1F2
            )
            content = f"<@{discord_user_id}> 你订阅的用户发布了新推文！"
        else:
            # 新关注提醒
            embed = discord.Embed(
                title=f"➕ 新关注提醒：{target_user_info['name']} (@{target_username})",
                description=f"刚刚关注了 **{data['name']} (@{data['username']})**\n\n**简介**：\n{data.get('description', '无')}",
                url=f"https://x.com/{data['username']}",
                color=0x00FF00
            )
            content = f"<@{discord_user_id}> 你监控的用户有了新关注！"
            
        embed.set_footer(text=f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 将发送任务添加到队列
        await queue_manager.add_task(
            "discord_bot",
            self._send_discord_message,
            target_channel_id, content, embed
        )
