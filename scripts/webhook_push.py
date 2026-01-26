import asyncio
import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import Config
from app.core.logger import logger
from app.engine import ScraperEngine

async def main():
    logger.info("开始定时 Webhook 全局推送...")
    engine = ScraperEngine()
    try:
        # 只运行一次全局检查
        await engine.check_global_subscriptions()
        # 保存 ID
        Config.save_processed_ids(engine.processed_ids)
        logger.info("Webhook 推送完成")
    except Exception as e:
        logger.error(f"推送过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
