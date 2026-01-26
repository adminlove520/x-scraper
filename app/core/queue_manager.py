import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple
from app.core.config import Config

logger = logging.getLogger(__name__)

class QueueManager:
    """
    异步队列管理器，用于处理各种API请求和消息发送，实现速率限制和重试机制
    """
    
    def __init__(self):
        # 队列类型定义
        self.queue_types = ["twitter_api", "discord_bot", "webhook_push"]
        
        # 创建队列字典
        self.queues: Dict[str, asyncio.Queue] = {
            queue_type: asyncio.Queue() for queue_type in self.queue_types
        }
        
        # 从配置中获取速率限制（请求数/时间窗口秒）
        self.rate_limits = {
            "twitter_api": (Config.QUEUE_CONFIG["twitter_api"]["max_tokens"], Config.QUEUE_CONFIG["twitter_api"]["refill_interval"]),
            "discord_bot": (Config.QUEUE_CONFIG["discord_bot"]["max_tokens"], Config.QUEUE_CONFIG["discord_bot"]["refill_interval"]),
            "webhook_push": (Config.QUEUE_CONFIG["webhook_push"]["max_tokens"], Config.QUEUE_CONFIG["webhook_push"]["refill_interval"])
        }
        
        # 令牌桶存储
        self.tokens: Dict[str, int] = {
            queue_type: self.rate_limits[queue_type][0] for queue_type in self.queue_types
        }
        
        # 最后补充令牌时间
        self.last_refill: Dict[str, float] = {
            queue_type: asyncio.get_event_loop().time() for queue_type in self.queue_types
        }
        
        # 运行状态
        self.is_running = False
        
        # 任务句柄
        self.tasks: List[asyncio.Task] = []
    
    async def start(self):
        """启动队列管理器，开始处理所有队列"""
        if self.is_running:
            return
        
        logger.info("队列管理器启动中...")
        self.is_running = True
        
        # 为每个队列启动一个处理器任务
        for queue_type in self.queue_types:
            task = asyncio.create_task(self._process_queue(queue_type))
            self.tasks.append(task)
        
        logger.info("队列管理器已启动")
    
    async def stop(self):
        """停止队列管理器"""
        if not self.is_running:
            return
        
        logger.info("队列管理器停止中...")
        self.is_running = False
        
        # 取消所有任务
        for task in self.tasks:
            task.cancel()
        
        # 等待所有任务完成
        try:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"停止队列管理器时发生错误: {e}")
        
        logger.info("队列管理器已停止")
    
    async def _refill_tokens(self, queue_type: str):
        """补充令牌桶中的令牌"""
        now = asyncio.get_event_loop().time()
        elapsed = now - self.last_refill[queue_type]
        
        if elapsed > 0:
            # 获取速率限制配置
            max_tokens, refill_interval = self.rate_limits[queue_type]
            
            # 计算可以补充的令牌数
            tokens_to_add = int(elapsed / refill_interval * max_tokens)
            
            if tokens_to_add > 0:
                # 更新令牌数量
                self.tokens[queue_type] = min(max_tokens, self.tokens[queue_type] + tokens_to_add)
                self.last_refill[queue_type] = now
    
    async def _wait_for_token(self, queue_type: str):
        """等待可用令牌"""
        while True:
            await self._refill_tokens(queue_type)
            
            if self.tokens[queue_type] > 0:
                # 消耗一个令牌
                self.tokens[queue_type] -= 1
                return
            
            # 等待直到下一个令牌可用
            _, refill_interval = self.rate_limits[queue_type]
            await asyncio.sleep(refill_interval / self.rate_limits[queue_type][0])
    
    async def add_task(self, queue_type: str, task_func: Callable, *args, **kwargs):
        """
        添加任务到指定队列
        
        Args:
            queue_type: 队列类型
            task_func: 任务函数
            *args: 任务函数参数
            **kwargs: 任务函数关键字参数
        """
        if queue_type not in self.queues:
            logger.error(f"未知的队列类型: {queue_type}")
            return
        
        # 创建任务对象
        task = {
            "func": task_func,
            "args": args,
            "kwargs": kwargs,
            "retries": 0,
            "max_retries": 3
        }
        
        # 添加到队列
        await self.queues[queue_type].put(task)
        logger.debug(f"已添加任务到 {queue_type} 队列，当前队列大小: {self.queues[queue_type].qsize()}")
    
    async def _process_queue(self, queue_type: str):
        """处理指定队列的任务"""
        logger.info(f"开始处理 {queue_type} 队列")
        
        while self.is_running:
            try:
                # 等待可用令牌
                await self._wait_for_token(queue_type)
                
                # 从队列获取任务
                task = await self.queues[queue_type].get()
                
                try:
                    # 执行任务
                    logger.debug(f"执行 {queue_type} 任务，重试次数: {task['retries']}")
                    await task["func"](*task["args"], **task["kwargs"])
                except Exception as e:
                    logger.error(f"执行 {queue_type} 任务失败: {e}")
                    
                    # 重试逻辑
                    task["retries"] += 1
                    if task["retries"] < task["max_retries"]:
                        # 指数退避
                        wait_time = 2 ** (task["retries"] - 1)
                        logger.info(f"{queue_type} 任务将在 {wait_time} 秒后重试")
                        await asyncio.sleep(wait_time)
                        await self.queues[queue_type].put(task)
                    else:
                        logger.error(f"{queue_type} 任务重试次数耗尽")
                finally:
                    # 标记任务完成
                    self.queues[queue_type].task_done()
            
            except asyncio.CancelledError:
                logger.info(f"{queue_type} 队列处理器已取消")
                break
            except Exception as e:
                logger.error(f"{queue_type} 队列处理器发生错误: {e}")
                # 短暂暂停后继续
                await asyncio.sleep(1)
        
        logger.info(f"停止处理 {queue_type} 队列")
    
    def get_queue_size(self, queue_type: str) -> Optional[int]:
        """获取指定队列的大小"""
        if queue_type not in self.queues:
            return None
        return self.queues[queue_type].qsize()
    
    async def wait_for_empty_queues(self):
        """等待所有队列为空"""
        logger.info("等待所有队列为空...")
        for queue_type in self.queue_types:
            await self.queues[queue_type].join()
        logger.info("所有队列已为空")

# 创建全局队列管理器实例
queue_manager = QueueManager()
