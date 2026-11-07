"""
用来操作向量数据库的客户端管理器
"""
from typing import Optional

from app.conf import app_config
from app.conf.app_config import QdrantConfig
from qdrant_client import AsyncQdrantClient, models


class QdrantClientMager:
    def __init__(self,config:QdrantConfig):
        self.config = config
        self.client : Optional[AsyncQdrantClient]= None

    def create_client(self):
        self.client = AsyncQdrantClient(f"http://{self.config.host}:{self.config.port}")

    async def close(self):
        await self.client.close()

qdrant_client_manager = QdrantClientMager(app_config.qdrant)