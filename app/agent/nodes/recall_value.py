from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from app.core.log import logger
from app.models.es.value_info_es import ValueInfoES
from app.prompt.prompt_loader import load_prompt

"""
1.利用大模型进行语义化提取关键字 keywords，理由jieba提取字面上的关键字（要把问题原文放在关键字列表中）
3.keywords_vector 去 ES 搜索匹配的字段值信息。list[ValueInfoES]
4.去重合并字段信息得到 recall_values:list[ValueInfoES]
5.返回 recall_values

"""

async def recall_value(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    #自定义输出
    runtime.stream_writer("召回字段值")
    try:
        query = state["query"]
        keywords = state["keywords"]
        value_es_repo = runtime.context["value_es_repo"]
        #1.利用大模型进行语义化提取关键字 keywords，利用jieba提取字面上的关键字（要把问题原文放在关键字列表中）
        recall_prompt = PromptTemplate(
            template = load_prompt("extend_keywords_for_value_recall"),
            input_variables=[query]
        )
        output_parsers = JsonOutputParser()
        chain = recall_prompt | llm | output_parsers
        result = chain.invoke({"query": query }) # list[keywords,]
        logger.info(f"recall_value llm keywords:{result}")
        keywords = list(set(result+keywords))

        value_infos_dict : dict[str,ValueInfoES] = {}

        #3.每个keywords_vector 去qdrant 搜索匹配的字段值信息。list[ValueInfoES]
        for  keyword in keywords:
            value_infos :list[ValueInfoES] = await value_es_repo.search(keyword)
            #4.去重合并字段值信息得到 recall_values:list[ValueInfoES]
            for value_info in  value_infos:
                value_id = value_info["id"]
                if value_id not in value_infos_dict:
                    value_infos_dict[value_id] = value_info
        recall_values = list(value_infos_dict.values())
        #5.返回 recall_values list[ValueInfoES]
        logger.info(f"召回字段值完成：{recall_values}")
        return {"recall_values":recall_values}
    except Exception as e:
        logger.error(f"召回字段值失败：f{str(e)}")
        raise