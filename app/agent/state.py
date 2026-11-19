from typing import TypedDict


class DataAgentState(TypedDict):
    query:str
    keywords:str
    sql: str
    error:str