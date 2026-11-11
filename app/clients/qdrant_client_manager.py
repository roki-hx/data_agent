"""
用来操作向量数据库的客户端管理器
"""
import asyncio
import random
from typing import Optional

from app.conf.app_config import QdrantConfig, app_config
from qdrant_client import AsyncQdrantClient, models


class QdrantClientMager:
    def __init__(self,config: QdrantConfig):
        self.config = config
        self.client : Optional[AsyncQdrantClient]= None

    def create_client(self):
        self.client = AsyncQdrantClient(f"http://{self.config.host}:{self.config.port}")

    async def close(self):
        await self.client.close()

qdrant_client_manager = QdrantClientMager(app_config.qdrant)


if __name__ == '__main__':
    async def test_qdrant():
        qdrant_client_manager.create_client()
        client = qdrant_client_manager.client
        collection_name = "collection1"
        if await client.collection_exists(collection_name):
            await client.delete_collection(collection_name)
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
        )

        # 插入向量
        await client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=i,  # 标识id
                    payload={
                        "color": "red" if i % 2 == 0 else "blue",
                    },
                    # 生成10维随机向量
                    vector=[random.random() for _ in range(1024)],
                )
                for i in range(100)  # 创建100个向量
            ],
        )

        # 搜索向量： 查找最相似的10个向量
        result = await client.query_points(
            collection_name=collection_name,
            query=[random.random() for _ in range(1024)],  # 生成一个10维随机向量 用于查询
            limit=9,  # 返回的最相似的9个向量
            # query_filter=models.Filter(
            #     must=[models.FieldCondition(key="color", match=models.MatchValue(value="red"))]
            # ),
            score_threshold=0.5  # 向量相似度阈值，低于该阈值的向量将被忽略
        )

        print(result.points)
        print(len(result.points))

        for point in result.points:
            print(f"reload={point.payload}")



        await qdrant_client_manager.close()


    asyncio.run(test_qdrant())