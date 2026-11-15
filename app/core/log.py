import asyncio
import sys
from pathlib import Path

from loguru import logger

from app.conf.app_config import app_config
from app.core.context import get_req_id, set_req_id

"""
# 定制日志输出格式，控制输出级别
# 自动将日志内容保存到日志文件
# 指定日志文件的最大大小，一旦超过自动创建一个新的的文件
# 指定文件的有效期，过了自动删除
# 记录当前日志输出是哪个请求的，记录请求id
"""

# 配置日志格式
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "  # 绿色显示日志时间（精确到毫秒）
    "<level>{level: <8}</level> | "  # 按级别颜色显示日志级别（左对齐，占8个字符）
    "<magenta>request_id - {extra[request_id]}</magenta> | "  # 品红色显示request_id（从日志extra中获取）
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "  # 青色显示日志所在文件、函数、行号
    "<level>{message}</level>"  # 按级别颜色显示日志正文
)

def inject_request_id(record):
   # 获取当前请求id
    request_id = get_req_id()
    # 将 request_id 存入日志记录的 extra 字段，供日志格式中 {extra[request_id]} 调用
    record["extra"]["request_id"] = request_id

# 移除默认配置
logger.remove()

# 给日志打补丁，使其在输出每条日志前执行inject_request_id函数，注入request_id
logger = logger.patch(inject_request_id)

#配置是否设置了控制台输出
if app_config.logging.console.enable:
    logger.add(sink=sys.stdout,level=app_config.logging.console.level,format=log_format)

if app_config.logging.file.enable:
    # 解析日志文件存储路径
    path = Path(app_config.logging.file.path)

    # 递归创建日志目录（如果不存在），已存在则不报错
    path.mkdir(parents=True, exist_ok=True)

    logger.add(
        sink= path / "app.log",  # 日志文件完整路径
        level=app_config.logging.file.level,  # 文件日志输出级别
        format=log_format,  # 使用自定义的日志格式
        rotation=app_config.logging.file.rotation,  # 日志文件分割规则（如按大小/时间）
        retention=app_config.logging.file.retention,  # 日志文件保留时长
        encoding="utf-8"  # 日志文件编码格式
    )

if __name__ == '__main__':
    async def  req1():
        # 接收到请求
        set_req_id("111")
        # 模拟处理
        await asyncio.sleep(1)
        logger.info(get_req_id())

    async def req2():
        # 接收到请求
        set_req_id("222")
        # 模拟处理
        await asyncio.sleep(1)
        logger.info(get_req_id())


    async def test():
        await asyncio.gather(req1(), req2())

    asyncio.run(test())