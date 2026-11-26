from qdrant_client import AsyncQdrantClient,models

from app.conf.app_config import app_config
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant

"""
用来操作qdrant数据库中的指标信息
"""
class ColumnQdrantRepository:
    collection_name = "data-agent_column_collection"
    def __init__(self,client : AsyncQdrantClient):
        self.client = client

    #创建集合，存在即删除
    async def create_collection(self):
        client = self.client
        collection_name = self.collection_name
        if await client.collection_exists(collection_name):
            await client.delete_collection(collection_name)
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=app_config.qdrant.embedding_size,
                distance=models.Distance.COSINE),
        )

    #批量插入字段数据信息及其向量
    async def insert_column_info_vectors(self,ids:list[str]
                                         ,payloads:list[ColumnInfoQdrant]
                                         ,vectors:list[list[float]]):
        client =self.client
        collection_name = self.collection_name

        #确保创建了集合
        await self.create_collection()

        #分批次处理
        batch_size = 10
        for i in range(0,len(ids),batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_payloads = payloads[i:i+batch_size]
            batch_vectors = vectors[i:i+batch_size]

            # 批量插入向量
            await client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=batch_ids[i],  # 标识id
                        payload=batch_payloads[i],
                        # 生成1024维随机向量
                        vector=batch_vectors[i],
                    )
                    for i in range(len(batch_ids))
                ],
            )
    #搜索查询方法
    async def search(self,keyword_vector:list[float]) ->list[ColumnInfoQdrant]:
        # 搜索向量： 查找最相似的10个向量
        results = await self.client.query_points(
            collection_name= self.collection_name,
            query=keyword_vector,
            limit=9,  # 返回的最相似的9个向量
            score_threshold=0.6,  # 向量相似度阈值，低于该阈值的向量将被忽略
        )
        return [ColumnInfoQdrant(**result.payload)  for result in results.points] #解包一个字典 放在一个对象中
