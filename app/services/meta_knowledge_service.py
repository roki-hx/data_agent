from app.conf.meta_config import meta_config, TableConfig, MetricConfig
from app.core.log import logger
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
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
        self._save_metric_infos_qdrant(metric_infos)
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
    async def _save_column_infos_to_qdrant(self, column_infos:list[ColumnInfoMySQL]):
        pass

    async def _save_values_infos_to_es(self, column_infos:list[ColumnInfoMySQL], tables:list[TableConfig]):
        pass
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

    def _save_metric_infos_qdrant(self, metric_infos:list[MetricInfoMySQL]):
        pass