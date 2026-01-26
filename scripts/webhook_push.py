import asyncio
import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import Config
from app.core.logger import logger
from app.engine import ScraperEngine
from app.core.queue_manager import queue_manager

async def main():
    logger.info("开始定时 Webhook 全局推送...")
    engine = ScraperEngine()
    try:
        # 启动队列管理器
        await queue_manager.start()
        
        # 只运行一次全局检查
        await engine.check_global_subscriptions()
        
        # 保存 ID
        Config.save_processed_ids(engine.processed_ids)
        
        # 等待队列处理完成
        await queue_manager.wait_for_empty_queues()
        
        logger.info("Webhook 推送完成")
    except Exception as e:
        logger.error(f"推送过程中发生错误: {e}")
    finally:
        # 停止队列管理器
        await queue_manager.stop()
        
        # 关闭crawler会话
        await engine.crawler.close()
        
        # 关闭webhook_pusher会话
        await engine.webhook_pusher.close()

if __name__ == "__main__":
    asyncio.run(main())
