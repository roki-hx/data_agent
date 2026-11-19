from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from app.core.log import logger


def filter_metric(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    #自定义输出
    runtime.stream_writer("过滤指标")
    try:
        return {}
    except Exception as e:
        logger.error(f"过滤指标失败：f{str(e)}")
        raise