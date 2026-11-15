from sqlalchemy.ext.asyncio import AsyncSession

"""
dw数据库的持久层模块
"""
class DWMysqlRepository:
    def __init__(self , session : AsyncSession):
        self.session = session