from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from app.core.log import logger


def correct_sql(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    #自定义输出
    runtime.stream_writer("修正SQL")
    try:
        return {}
    except Exception as e:
        logger.error(f"修正SQL失败：f{str(e)}")
        raise