from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from app.core.log import logger


def generate_sql(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    #自定义输出
    runtime.stream_writer("生成SQL")
    try:
        return {}
    except Exception as e:
        logger.error(f"生成SQL失败：f{str(e)}")
        raise