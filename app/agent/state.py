from typing import TypedDict

from app.models.es.value_info_es import ValueInfoES
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant


class DataAgentState(TypedDict):
    query:str
    keywords:str
    sql: str
    error:str
    recall_columns:list[ColumnInfoQdrant]
    recall_metrics: list[MetricInfoQdrant]
    recall_values: list[ValueInfoES]