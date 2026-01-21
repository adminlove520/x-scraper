import discord
from discord import app_commands
from discord.ext import commands
from app.core.config import Config
from app.core.logger import logger
from app.crawlers.x_crawler import XCrawler
from app.services.user_service import UserService

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.crawler = XCrawler()
        self.user_service = UserService(crawler=self.crawler)

    async def setup_hook(self):
        # 同步 Slash Commands
        await self.tree.sync()
        logger.info("Discord Bot Slash Commands 已同步")

    async def on_ready(self):
        logger.info(f"Discord Bot 已登录为 {self.user}")

def is_admin():
    async def predicate(interaction: discord.Interaction):
        is_admin = str(interaction.user.id) == Config.DISCORD_ADMIN_ID
        if not is_admin:
            await interaction.response.send_message("❌ 该命令仅限管理员使用。", ephemeral=True)
        return is_admin
    return app_commands.check(predicate)

# 初始化 Bot
bot = DiscordBot()

@bot.tree.command(name="admin_followers_list", description="查看当前订阅的 X 用户列表")
async def admin_followers_list(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    # 尝试加载当前用户的专有订阅
    user_configs = Config.get_dc_user_configs()
    current_user_config = next((c for c in user_configs if c["id"] == user_id), None)
    
    if not current_user_config or not current_user_config["users"]:
        await interaction.response.send_message("你目前没有任何订阅用户。", ephemeral=True)
        return
    
    users_list = "\n".join([f"- @{u['username']}" for u in current_user_config["users"]])
    await interaction.response.send_message(f"你的订阅列表：\n{users_list}", ephemeral=True)

@bot.tree.command(name="followers_add", description="增加订阅用户")
@app_commands.describe(username="推特用户名，如 @elonmusk")
async def followers_add(interaction: discord.Interaction, username: str):
    user_id = str(interaction.user.id)
    username = username.lstrip('@')
    
    await interaction.response.defer(ephemeral=True)

    # 验证并获取增强元数据
    metadata = bot.user_service.get_user_metadata(username)
    if not metadata.get("id"):
        await interaction.followup.send(f"未找到用户 @{username}，请检查拼写。", ephemeral=True)
        return
    
    # 加载并更新配置
    user_configs = Config.get_dc_user_configs()
    current_user_config = next((c for c in user_configs if c["id"] == user_id), {"id": user_id, "users": []})
    
    # 防止重复
    if any(u['username'].lower() == username.lower() for u in current_user_config["users"]):
        await interaction.followup.send(f"你已经订阅了 @{username}。", ephemeral=True)
        return
    
    # 使用增强元数据
    current_user_config["users"].append(metadata)
    
    if Config.save_dc_user_config(user_id, current_user_config["users"]):
        tags_str = ", ".join(metadata['tags']) if metadata['tags'] else "无"
        await interaction.followup.send(
            f"✅ 成功订阅 **{metadata.get('name', username)}** (@{username})！\n"
            f"📊 优先级: `{metadata['priority']}` | 标签: `{tags_str}`\n"
            f"💡 已为您自动识别并配置元数据。", 
            ephemeral=True
        )
    else:
        await interaction.followup.send("❌ 订阅失败，请检查数据目录权限。", ephemeral=True)

@bot.tree.command(name="followers_delete", description="删除订阅用户")
@app_commands.describe(username="推特用户名，如 @elonmusk")
async def followers_delete(interaction: discord.Interaction, username: str):
    user_id = str(interaction.user.id)
    username = username.lstrip('@')
    
    user_configs = Config.get_dc_user_configs()
    current_user_config = next((c for c in user_configs if c["id"] == user_id), None)
    
    if not current_user_config or not current_user_config["users"]:
        await interaction.response.send_message("你目前没有任何订阅用户。", ephemeral=True)
        return
    
    initial_count = len(current_user_config["users"])
    current_user_config["users"] = [u for u in current_user_config["users"] if u['username'].lower() != username.lower()]
    
    if len(current_user_config["users"]) == initial_count:
        await interaction.response.send_message(f"你的订阅列表中没有 @{username}。", ephemeral=True)
        return
    
    if Config.save_dc_user_config(user_id, current_user_config["users"]):
        await interaction.response.send_message(f"❌ 已成功取消订阅 @{username}。", ephemeral=True)
    else:
        await interaction.response.send_message("操作失败，请重试。", ephemeral=True)

@bot.tree.command(name="admin_all_stats", description="[管理员] 查看所有用户的订阅统计")
@is_admin()
async def admin_all_stats(interaction: discord.Interaction):
    user_configs = Config.get_dc_user_configs()
    if not user_configs:
        await interaction.response.send_message("目前没有任何用户有订阅。", ephemeral=True)
        return

    message = "📋 **全站订阅统计 (仅限管理员)**\n"
    total_subs = 0
    for config in user_configs:
        sub_count = len(config["users"])
        total_subs += sub_count
        message += f"- 用户 <@{config['id']}>: {sub_count} 个订阅\n"
    
    message += f"\n**总计**: {len(user_configs)} 名用户, {total_subs} 个 X 订阅项目"
    await interaction.response.send_message(message, ephemeral=True)

@bot.tree.command(name="admin_view_user", description="[管理员] 查看指定用户的订阅列表")
@app_commands.describe(user="要查看的 Discord 用户")
@is_admin()
async def admin_view_user(interaction: discord.Interaction, user: discord.User):
    user_id = str(user.id)
    user_configs = Config.get_dc_user_configs()
    current_user_config = next((c for c in user_configs if c["id"] == user_id), None)
    
    if not current_user_config or not current_user_config["users"]:
        await interaction.response.send_message(f"用户 {user.display_name} 没有任何订阅。", ephemeral=True)
        return
    
    users_list = "\n".join([f"- @{u['username']} ({u['name']})" for u in current_user_config["users"]])
    await interaction.response.send_message(f"用户 <@{user_id}> 的订阅列表：\n{users_list}", ephemeral=True)

@bot.tree.command(name="admin_delete_for_user", description="[管理员] 强制删除指定用户的某个订阅")
@app_commands.describe(user="Discord 用户", twitter_username="推特用户名")
@is_admin()
async def admin_delete_for_user(interaction: discord.Interaction, user: discord.User, twitter_username: str):
    user_id = str(user.id)
    username = twitter_username.lstrip('@')
    
    user_configs = Config.get_dc_user_configs()
    current_user_config = next((c for c in user_configs if c["id"] == user_id), None)
    
    if not current_user_config or not current_user_config["users"]:
        await interaction.response.send_message(f"用户 {user.display_name} 没有任何订阅。", ephemeral=True)
        return
    
    initial_count = len(current_user_config["users"])
    current_user_config["users"] = [u for u in current_user_config["users"] if u['username'].lower() != username.lower()]
    
    if len(current_user_config["users"]) == initial_count:
        await interaction.response.send_message(f"用户 {user.display_name} 的列表中没有 @{username}。", ephemeral=True)
        return
    
    if Config.save_dc_user_config(user_id, current_user_config["users"]):
        await interaction.response.send_message(f"✅ 管理员操作：已为 <@{user_id}> 取消订阅 @{username}。", ephemeral=True)
    else:
        await interaction.response.send_message("操作失败。", ephemeral=True)

@bot.tree.command(name="followtop10", description="按粉丝数排序查看 Top 10 订阅用户")
async def followtop10(interaction: discord.Interaction):
    await interaction.response.defer()
    
    user_id = str(interaction.user.id)
    user_configs = Config.get_dc_user_configs()
    current_user_config = next((c for c in user_configs if c["id"] == user_id), None)
    
    if not current_user_config or not current_user_config["users"]:
        await interaction.followup.send("你目前没有任何订阅用户。", ephemeral=True)
        return
    
    usernames = [u["username"] for u in current_user_config["users"]]
    top_users = bot.crawler.get_top_users(usernames)
    
    if not top_users:
        await interaction.followup.send("获取数据失败。", ephemeral=True)
        return
    
    message = "📊 **你的订阅用户粉丝排行榜 Top 10**\n\n"
    for i, user in enumerate(top_users):
        message += "################\n"
        message += f"TOP{i+1}\n"
        message += f"->名称：{user['name']}\n"
        message += f"->用户名：{user['username']} (https://x.com/{user['username']})\n"
        message += f"->粉丝数：{user['public_metrics']['followers_count']}\n"
        message += f"->简介：{user.get('description', '无')}\n"
        message += "################\n"
    
    await interaction.followup.send(message)

# 辅助函数：启动 Bot
def start_bot():
    if not Config.DISCORD_TOKEN:
        logger.error("未配置 DISCORD_TOKEN")
        return
    bot.run(Config.DISCORD_TOKEN)
