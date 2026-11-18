import uuid

from app.conf.meta_config import meta_config, TableConfig, MetricConfig
from app.core.log import logger
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from app.models.es.value_info_es import ValueInfoES
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaKnowledgeService:
    def __init__(
        self,
        dw_mysql_repo : DWMysqlRepository,
        meta_mysql_repo :MetaMysqlRepository,
        value_es_repo : ValueESRepository,
        column_qdrant_repo : ColumnQdrantRepository,
        metric_qdrant_repo : MetricQdrantRepository,
        embedding_client : HuggingFaceEndpointEmbeddings
    ):
        self.dw_mysql_repo = dw_mysql_repo
        self.meta_mysql_repo =meta_mysql_repo
        self.value_es_repo = value_es_repo
        self.column_qdrant_repo = column_qdrant_repo
        self.metric_qdrant_repo = metric_qdrant_repo
        self.embedding_client = embedding_client

    #构建元数据知识库的业务方法

    """
    # 1. 处理表相关的信息
    # 1.1 将表的信息和字段的信息保存到meta库（tableinfo和column_info表）
    # 1.2 对所有字段信息建立向量索引
    # 1.3 对象字段取值建立全文索引
    # 2. 处理指标信息
    # 2.1 将指标信息数据保存到meta库（metric_info和culumn_metric表）
    # 2.2 对指标信息建立向量索引
    """
    async def build(self):
        logger.info("执行构建元数据知识库业务")
        # 1. 处理表相关的信息
        # 1.1 将表的信息和字段的信息保存到meta库（table_info和column_info表）
        column_infos :list[ColumnInfoMySQL]= await self._save_table_infos_to_meta_db(meta_config.tables)
        logger.info("将表的信息和字段的信息保存到meta库")
        # 1.2 对所有字段信息建立向量索引
        await self._save_column_infos_to_qdrant(column_infos)
        logger.info("对所有字段信息建立向量索引")
        # 1.3 对字段取值建立全文索引
        await self._save_values_infos_to_es(column_infos,meta_config.tables)
        logger.info("对字段取值建立全文索引")
        # 2. 处理指标信息
        # 2.1 将指标信息数据保存到meta库（metric_info和column_metric表）
        metric_infos :list[MetricInfoMySQL] = await self._save_metric_infos_to_mate(meta_config.metrics)
        logger.info("将指标信息数据保存到meta库")
        # 2.2 对指标信息建立向量索引
        await self._save_metric_infos_qdrant(metric_infos)
        logger.info("对指标信息建立向量索引")

    async def _save_table_infos_to_meta_db(self, tables:list[TableConfig])-> list[ColumnInfoMySQL]:
        table_infos: list[TableInfoMySQL] =[]
        column_infos: list[ColumnInfoMySQL] =[]
        for table in tables:
            table_infos.append(TableInfoMySQL(
                id=table.name,
                name=table.name,
                role=table.role,
                description=table.description,
            ))
            #查表
            column_types= await self.dw_mysql_repo.get_column_types(table.name)
            for column in table.columns:
                values:list = await self.dw_mysql_repo.get_column_values(table.name,column.name)
                column_infos.append(ColumnInfoMySQL(
                    id=f"{table.name}.{column.name}",
                    name=column.name,
                    type=column_types[column.name],#需要查表
                    role=column.role,
                    examples=values,#需要查表
                    description=column.description,
                    alias=column.alias,
                    table_id=table.name
                ))

        self.meta_mysql_repo.save_table_infos(table_infos)
        self.meta_mysql_repo.save_column_infos(column_infos)

        return column_infos

    #对字段信息建立向量索引
    async def _save_column_infos_to_qdrant(self, column_infos:list[ColumnInfoMySQL]):
        # 准备一个数组容器，存储一个字典对象（id, payload, 待向量化文本）
        data_dict_list: list[dict] = []
        #遍历column_infos得到(ids,payloads,vectors)
        for column_info in column_infos:
            column_info_qdrant = ColumnInfoQdrant(
                id=column_info.id,
                name=column_info.name,
                type=column_info.type,
                role=column_info.role,
                examples=column_info.examples,
                description=column_info.description,
                alias=column_info.alias,
                table_id=column_info.table_id
            )
            #name要向量化
            data_dict_list.append({
                "id": uuid.uuid4(),
                "payload":column_info_qdrant,
                "embedding_text": column_info.name,
            })
            #description要向量化
            data_dict_list.append({
                "id": uuid.uuid4(),
                "payload":column_info_qdrant,
                "embedding_text": column_info.description,
            })
            #alias要向量化
            for alia in  column_info.alias:
                data_dict_list.append({
                    "id": uuid.uuid4(),
                    "payload":column_info_qdrant,
                    "embedding_text": alia,
                })
            embedding_texts = [data_dict["embedding_text"]  for data_dict in data_dict_list]

            batch_size = 8
            vectors:list[list[float]] = []
            for i in range(0,len(embedding_texts),batch_size):
                batch_embedding_texts = embedding_texts[i:i+batch_size]
                batch_vectors: list[list[float]] = await self.embedding_client.aembed_documents(batch_embedding_texts)
                vectors.extend(batch_vectors)
            # 从上面的数组容器中取出所有id组成数组：ids: list[str]
            ids: list[str] = [data_dict["id"] for data_dict in data_dict_list]

            # 从上面的数组容器中取出所有payload组成数组：payloads: list[dict]
            payloads: list[dict] = [data_dict["payload"] for data_dict in data_dict_list]

            #执行insert_column_info_vectors(ids,payloads,vectors)
            await self.column_qdrant_repo.insert_column_info_vectors(ids=ids,payloads=payloads,vectors=vectors)

    #对字段取值建立全文索引
    async def _save_values_infos_to_es(self, column_infos:list[ColumnInfoMySQL], tables:list[TableConfig]):
        #准备数据
        values_infos :list[ValueInfoES] = []
        #获取字段是否需要建立索引
        column_sync_dict:dict[str,bool]={}
        for table in tables:
            for column in table.columns:
                column_sync_dict[f"{table.name}.{column.name}"] = column.sync

        for column in column_infos:
            if column_sync_dict[column.id]:
                #查询当前字段所有值
                values = await self.dw_mysql_repo.get_column_values(column.table_id,column_name=column.name,limit=10000)
                #为每个值创建ValueInfoES对象传给es保存
                for value in values:
                    values_infos.append(ValueInfoES(
                        id=f"{column.id}.{value}",
                        value=value,
                        type=column.type,
                        column_id=column.id,
                        column_name=column.name,
                        table_id=column.table_id,
                        table_name=column.table_id
                    ))
        #执行插入es
        await self.value_es_repo.insert_value_infos(values_infos)


    # 将指标信息数据保存到meta库（metric_info和column_metric表） 完成
    async def  _save_metric_infos_to_mate(self, metrics:list[MetricConfig])-> list[MetricInfoMySQL]:
        # 收集指标信息和字段指标
        metrics_infos: list[MetricInfoMySQL] = []
        column_metrics: list[ColumnMetricMySQL] = []
        for metric in metrics:
            metrics_infos.append(
                MetricInfoMySQL(
                    id=metric.name,
                    name=metric.name,
                    description=metric.description,
                    relevant_columns=metric.relevant_columns,
                    alias=metric.alias
                )
            )
            for column_id in metric.relevant_columns:
                column_metrics.append(ColumnMetricMySQL(
                    column_id= column_id,
                    metric_id = metric.name
                ))
        #调用持久层保存到库中
        self.meta_mysql_repo.save_metric_infos(metrics_infos)
        self.meta_mysql_repo.save_column_metric_infos(column_metrics)

        return metrics_infos

    async def _save_metric_infos_qdrant(self, metric_infos:list[MetricInfoMySQL]):
        # 准备一个数组容器，存储一个字典对象（id, payload, 待向量化文本）
        data_dict_list: list[dict] = []
        # 遍历 metric_infos 得到(ids,payloads,vectors)
        for metric_info in metric_infos:
            metric_info_qdrant = MetricInfoQdrant(
                id=metric_info.id,
                name=metric_info.name,
                description=metric_info.description,
                alias=metric_info.alias,
                relevant_columns=metric_info.relevant_columns
            )
            # name要向量化
            data_dict_list.append({
                "id": uuid.uuid4(),
                "payload": metric_info_qdrant,
                "embedding_text": metric_info.name,
            })
            # description要向量化
            data_dict_list.append({
                "id": uuid.uuid4(),
                "payload": metric_info_qdrant,
                "embedding_text": metric_info.description,
            })
            # alias要向量化
            for alia in metric_info.alias:
                data_dict_list.append({
                    "id": uuid.uuid4(),
                    "payload": metric_info_qdrant,
                    "embedding_text": alia,
                })
            embedding_texts = [data_dict["embedding_text"] for data_dict in data_dict_list]

            batch_size = 8
            vectors: list[list[float]] = []
            for i in range(0, len(embedding_texts), batch_size):
                batch_embedding_texts = embedding_texts[i:i + batch_size]
                batch_vectors: list[list[float]] = await self.embedding_client.aembed_documents(batch_embedding_texts)
                vectors.extend(batch_vectors)
            # 从上面的数组容器中取出所有id组成数组：ids: list[str]
            ids: list[str] = [data_dict["id"] for data_dict in data_dict_list]

            # 从上面的数组容器中取出所有payload组成数组：payloads: list[dict]
            payloads: list[dict] = [data_dict["payload"] for data_dict in data_dict_list]

            # 执行insert_column_info_vectors(ids,payloads,vectors)
            await self.metric_qdrant_repo.insert_metric_info_vectors(ids=ids, payloads=payloads, vectors=vectors)