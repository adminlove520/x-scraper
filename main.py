import asyncio
import threading
from app.core.config import Config
from app.core.logger import logger
from app.engine import ScraperEngine
from app.pushers.discord_bot import bot, start_bot

async def run_engine():
    """在后台运行采集引擎"""
    engine = ScraperEngine()
    # 默认每 5 分钟检查一次
    await engine.run_periodic_check(interval_seconds=300)

async def main():
    logger.info("X-Scraper 服务启动中...")
    
    # 启动采集引擎后台任务
    engine_task = asyncio.create_task(run_engine())
    
    # 启动 Discord Bot
    # 由于 bot.run 是阻塞的，我们可以在主异步函数中直接运行它（如果它是异步的）
    # 或者用 bot.start()
    try:
        if Config.DISCORD_TOKEN:
            await bot.start(Config.DISCORD_TOKEN)
        else:
            logger.warning("未检测到 DISCORD_TOKEN，Bot 功能将不可用")
            # 如果没有 Bot，我们只需等待引擎任务
            await engine_task
    except Exception as e:
        logger.error(f"运行过程中发生错误: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务已停止")
