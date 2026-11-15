
import asyncio
from typing import Optional

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from app.conf.app_config import EmbeddingConfig, app_config

"""
用于生成embedding向量的客户端管理器
"""
class EmbeddingClientManager():
    def __init__(self,config : EmbeddingConfig):
        self.config = config
        self.client :Optional[HuggingFaceEndpointEmbeddings] = None

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def create_client(self):
        self.client = HuggingFaceEndpointEmbeddings(model=f"http://{self.config.host}:{self.config.port}")

    # def close(self):
    #
embedding_client_manager = EmbeddingClientManager(app_config.embedding)

if __name__ == '__main__':
    async def test():
        # 初始化客户端
        embedding_client_manager.create_client()

        # 对单个文本内容进行异步向量化
        result = await embedding_client_manager.client.aembed_query("hello")
        print(result)
        print(len(result))

        # 对多个文本内容进行异步批量向量化
        result2 = await embedding_client_manager.client.aembed_documents(["hello", "world"])
        print(result2)
        print(len(result2))

    asyncio.run(test())