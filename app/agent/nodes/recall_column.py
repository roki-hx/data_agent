from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from app.core.log import logger


def recall_column(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    #自定义输出
    runtime.stream_writer("召回字段")
    try:
        return {}
    except Exception as e:
        logger.error(f"召回字段失败：f{str(e)}")
        raise