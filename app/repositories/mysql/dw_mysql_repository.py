from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

"""
dw数据库的持久层模块
"""
class DWMysqlRepository:
    def __init__(self , session : AsyncSession):
        self.session = session
    #获取指定表中的所有字段类型
    async def get_column_types(self, table_name:str)-> dict[str,str]:
        sql= f"show columns from `{table_name}`"
        result = await self.session.execute(text(sql))
        return {row.Field: row.Type for row in result}

    # 获取指定表中的字段类型
    async def get_column_values(self,table_name:str,column_name:str ,limit:int = 10)->list:
        sql = f"select distinct  {column_name} from {table_name} limit {limit}"
        result = await self.session.execute(text(sql))
        return result.scalars().all()

if __name__ == '__main__':
    import asyncio

    from app.clients.mysql_client_manager import dw_mysql_manager

    async def test_get_column_types():
        dw_mysql_manager.create_client()
        assert dw_mysql_manager.session_factory
        try:
            async with dw_mysql_manager.session_factory() as session:
                repo = DWMysqlRepository(session)
                column_types = await repo.get_column_types("dim_customer")
                for column_name, column_type in column_types.items():
                    print(f"{column_name}: {column_type}")

                # 校验返回值是一个非空的“字段名 -> 字段类型”字典
                assert isinstance(column_types, dict)
                assert column_types, "字段类型字典不应为空"
                assert all(
                    isinstance(name, str) and isinstance(type_, str)
                    for name, type_ in column_types.items()
                ), "字段名和字段类型都应该是字符串"
                print(f"共 {len(column_types)} 个字段，测试通过")
        finally:
            await dw_mysql_manager.close()

    asyncio.run(test_get_column_types())
