from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from app.core.log import logger


def execute_sql(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    #自定义输出
    runtime.stream_writer("执行SQL")
    try:
        raise Exception("SQL语法出错") #模拟报错
        return {}
    except Exception as e:
        logger.error(f"执行SQL失败：f{str(e)}")
        return {"error":f"执行SQL失败：f{str(e)}"}