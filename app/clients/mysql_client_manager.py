"""
操作MySQL客户端的服务
"""
import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy import text, Select
from app.conf.app_config import DBConfig,app_config
from app.models.mysql.table_info_mysql import TableInfoMySQL


class MysqlClientManager:
    def __init__(self,config:DBConfig):
        self.config = config
        self.client: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None

    def _get_url(self):
        return f"mysql+asyncmy://{self.config.user}:{self.config.password}@{self.config.host}/{self.config.database}?charset=utf8mb4"

    def create_client(self):
        self.client = create_async_engine(
            self._get_url(),
            pool_size = 10, #连接池个数，默认是5个
            max_overflow = 5 # 临时链接最大个数
            )
        self.session_factory = async_sessionmaker(
            self.client,
            autoflush=False,  # 查询看不到前面未提交的修改
            autobegin=True,  # 自动开启事务
        )

    async def close(self):
        await self.client.dispose()

# dw客户端管理器
dw_mysql_manager = MysqlClientManager(app_config.db_dw)

# 创建mate客户端管理
meta_mysql_manager = MysqlClientManager(app_config.db_meta)


if __name__ == '__main__':

    async def test_orm1():
        #测试插入一条数据
        meta_mysql_manager.create_client()

        async with meta_mysql_manager.session_factory() as session:
            session:AsyncSession


            #更新数据
            table_info:TableInfoMySQL = await session.get(TableInfoMySQL,"dim_customer1")
            table_info.description="aaaa"
            # 删除数据
            await session.delete(table_info)

            await session.commit()

        await meta_mysql_manager.close()

    #测试ORM insert  select
    async def test_orm():
        #测试插入一条数据
        meta_mysql_manager.create_client()

        async with meta_mysql_manager.session_factory() as session:
            session:AsyncSession

            table_info1 = TableInfoMySQL(
                id="dim_customer1",
                name="dim_customer1",
                role="dim",
                description="客户信息维度表1"
            )
            table_info2 = TableInfoMySQL(
                id="dim_customer2",
                name="dim_customer2",
                role="dim",
                description="客户信息维度表2"
            )
            session.add_all([table_info1,table_info2])
            # 提交事务
            await session.commit()

            # 查询一条数据
            # table_info = await session.get(TableInfoMySQL, "dim_customer1")
            # print(table_info.description)
            #查询多条数据
            result = await session.execute(
                Select(TableInfoMySQL)
                .limit(2)
            )
            table_infos:list[TableInfoMySQL] = result.scalars().all()
            for info in table_infos:
                print(info.description)
            # print(table_infos[0].description)
        #测试插入多条数据

        #测试查询多条数据


        await meta_mysql_manager.close()

    async def test():
        dw_mysql_manager.create_client()
        """
        result.all()    返回 [row, row, row]  row是可迭代的对象
        result.mappings().all() 返回 [rowMapping, rowMapping, rowMapping]  rowMapping是包含一行数据的字段名和字段值的对象
        result.scalars().all() 所回 [val, val, val]  val是第一列值
        """
        assert dw_mysql_manager.session_factory
        async with dw_mysql_manager.session_factory() as session:
            sql = 'select * from dim_customer limit 2'
            result = await session.execute(text(sql))

            # rows = result.all()
            # print(rows,type(rows[0]))
            # print(rows[0].customer_name)
            # for row in rows:
            #     for val in row:
            #         print(val)

            rows = result.mappings().all()

            # rows = result.scalars().all()
            for val in rows:
                print(val)


        #关闭客户端
        await dw_mysql_manager.close()

    asyncio.run(test_orm1())