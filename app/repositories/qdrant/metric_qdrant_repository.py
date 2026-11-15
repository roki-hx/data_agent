from qdrant_client import AsyncQdrantClient

"""
用来操作qdrant数据库中的指标信息
"""
class MetricQdrantRepository:
    def __init__(self,client : AsyncQdrantClient):
        self.client = client