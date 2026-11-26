from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from app.core.log import logger
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.prompt.prompt_loader import load_prompt
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository

"""
1.利用大模型进行语义化提取关键字 keywords，理由jieba提取字面上的关键字（要把问题原文放在关键字列表中）
2.keywords 批量进行向量化， keywords_vector
3.keywords_vector 去qdrant 搜索匹配的字段信息。list[ColumnInfoQdrant]
4.去重合并字段信息得到 recall_columns:list[ColumnInfoQdrant]
5.返回 recall_columns

"""

async def recall_column(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    #自定义输出
    runtime.stream_writer("召回字段")
    try:
        query = state["query"]
        keywords = state["keywords"]
        column_qdrant_repo: ColumnQdrantRepository = runtime.context["column_qdrant_repo"]
        embedding_client: HuggingFaceEndpointEmbeddings = runtime.context["embedding_client"]
        #1.利用大模型进行语义化提取关键字 keywords，利用jieba提取字面上的关键字（要把问题原文放在关键字列表中）
        recall_prompt = PromptTemplate(
            template = load_prompt("extend_keywords_for_column_recall"),
            input_variables=[query]
        )
        output_parsers = JsonOutputParser()
        chain = recall_prompt | llm | output_parsers
        result = chain.invoke({"query": query }) # list[keywords,]
        logger.info(f"recall_column llm keywords:{result}")
        keywords = list(set(result+keywords))

        #2.keywords 批量进行向量化， keywords_vector
        keywords_vector = await embedding_client.aembed_documents(keywords)
        column_infos_dict : dict[str,ColumnInfoQdrant] = {}
        #3.每个keywords_vector 去qdrant 搜索匹配的字段信息。list[ColumnInfoQdrant]
        for  keyword_vector in keywords_vector:
            column_infos :list[ColumnInfoQdrant] = await column_qdrant_repo.search(keyword_vector)
            #4.去重合并字段信息得到 recall_columns:list[ColumnInfoQdrant]
            for column_info in  column_infos:
                column_id = column_info["id"]
                if column_id not in column_infos_dict:
                    column_infos_dict[column_id] = column_info
        recall_columns = list(column_infos_dict.values())
        #5.返回 recall_columns list[ColumnInfoQdrant]
        logger.info(f"召回字段信息完成：{recall_columns}")
        return {"recall_columns":recall_columns}
    except Exception as e:
        logger.error(f"召回字段失败：f{str(e)}")
        raise