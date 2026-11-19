from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from app.core.log import logger


def merge_retrieved_info(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    #自定义输出
    runtime.stream_writer("合并召回")
    try:
        return {}
    except Exception as e:
        logger.error(f"合并召回失败：f{str(e)}")
        raise