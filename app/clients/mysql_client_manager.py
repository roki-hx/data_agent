"""
操作MySQL客户端的服务
"""
from typing import Optional

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession

from app.conf.app_config import DBConfig,app_config


class MysqlClientManager:
    def __init__(self,config:DBConfig):
        self.config = config
        self.client: Optional[AsyncEngine] = None
    def _get_url(self):
        return f"mysql+asyncmy://{self.config.user}:{self.config.password}@{self.config.host}/{self.config.database}?charset=utf8mb4"

    def create_client(self):
        self.client = create_async_engine(self._get_url())

    async def close(self):
        await self.client.dispose()

# dw客户端管理器
dw_mysql_manager = MysqlClientManager(app_config.db_dw)

# 创建mate客户端管理
meta_mysql_manager = MysqlClientManager(app_config.db_meta)


if __name__ == '__main__':
    async def test():
        dw_mysql_manager.create_client()
        #关闭客户端
        await dw_mysql_manager.close()

    async with AsyncSession() as session:
        sql = '';
        await  session.execute()