from elasticsearch import AsyncElasticsearch
from elasticsearch.esql.functions import length

from app.clients.es_client_manager import es_client_manager
from app.models.es.value_info_es import ValueInfoES


class ValueESRepository:
    index_name = "data-agent-value_index"
    mappings = {
        "dynamic": False,
        "properties": {
            "id": {"type": "keyword","index":False},
            "value": {"type": "text", "analyzer": "ik_max_word", "search_analyzer": "ik_max_word","index":True},
            "type": {"type": "keyword","index":False},
            "column_id": {"type": "keyword","index":False},
            "column_name": {"type": "keyword","index":False},
            "table_id": {"type": "keyword","index":False},
            "table_name": {"type": "keyword","index":False},
        }
    }
    def __init__(self , client : AsyncElasticsearch):
        self.client = client

    async def create_index(self):
        client = self.client
        index_name = self.index_name
        mappings = self.mappings
        # 创建索引 存在则删除索引
        if await client.indices.exists(index=index_name):
            await client.indices.delete(index=index_name)
        result = await client.indices.create(
            index=index_name,
            mappings=mappings
        )

    #批量插入多个字段值信息
    async def insert_value_infos(self,values:list[ValueInfoES]):
        client = self.client
        index_name = self.index_name
        #确保存在索引
        await self.create_index()

        operations: list = []

        batch_size=30
        for i in range(0 ,len(values),batch_size):
            batch_values=values[i:i+batch_size]
            for value in batch_values:
                #遍历values
                operations.append({
                    "index": {
                        "_index": index_name
                    }
                })
                operations.append(value)

            #插入数据
            result = await client.bulk(
                operations=operations
            )

    async def search(self, keyword)->list[ValueInfoES]:
        result = await self.client.search(
            index=self.index_name,
            query={
                "match": {
                    "value": keyword
                }
            },
        )
        return  [ValueInfoES(**item["_source"]) for item in result["hits"]["hits"]]