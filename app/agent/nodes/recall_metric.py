from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from app.core.log import logger
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.prompt.prompt_loader import load_prompt
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository

"""
1.利用大模型进行语义化提取关键字 keywords，理由jieba提取字面上的关键字（要把问题原文放在关键字列表中）
2.keywords 批量进行向量化， keywords_vector
3.keywords_vector 去qdrant 搜索匹配的字段信息。list[MetricInfoQdrant]
4.去重合并字段信息得到 recall_metrics:list[MetricInfoQdrant]
5.返回 recall_metrics

"""

async def recall_metric(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    #自定义输出
    runtime.stream_writer("召回字段")
    try:
        query = state["query"]
        keywords = state["keywords"]
        metric_qdrant_repo: MetricQdrantRepository = runtime.context["metric_qdrant_repo"]
        embedding_client: HuggingFaceEndpointEmbeddings = runtime.context["embedding_client"]
        #1.利用大模型进行语义化提取关键字 keywords，利用jieba提取字面上的关键字（要把问题原文放在关键字列表中）
        recall_prompt = PromptTemplate(
            template = load_prompt("extend_keywords_for_metric_recall"),
            input_variables=[query]
        )
        output_parsers = JsonOutputParser()
        chain = recall_prompt | llm | output_parsers
        result = chain.invoke({"query": query }) # list[keywords,]
        logger.info(f"recall_metric llm keywords:{result}")
        keywords = list(set(result+keywords))

        #2.keywords 批量进行向量化， keywords_vector
        keywords_vector = await embedding_client.aembed_documents(keywords)
        metric_infos_dict : dict[str,MetricInfoQdrant] = {}
        #3.每个keywords_vector 去qdrant 搜索匹配的字段信息。list[MetricInfoQdrant]
        for  keyword_vector in keywords_vector:
            metric_infos :list[MetricInfoQdrant] = await metric_qdrant_repo.search(keyword_vector)
            #4.去重合并字段信息得到 recall_metrics:list[MetricInfoQdrant]
            for metric_info in  metric_infos:
                metric_id = metric_info["id"]
                if metric_id not in metric_infos_dict:
                    metric_infos_dict[metric_id] = metric_info
        recall_metrics = list(metric_infos_dict.values())
        #5.返回 recall_metrics list[MetricInfoQdrant]
        logger.info(f"召回指标信息完成：{recall_metrics}")
        return {"recall_metrics":recall_metrics}
    except Exception as e:
        logger.error(f"召回指标信息失败：f{str(e)}")
        raise