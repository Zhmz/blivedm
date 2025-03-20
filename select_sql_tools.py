from sql_const import *
import psycopg2
from psycopg2 import sql


def query_danmu_by_table_and_room_and_timespan(conn_params, table_name, room_id, start_ts, end_ts):
    """
    动态查询弹幕数据
    :param conn_params: 数据库连接参数（字典）
    :param table_name: 表名（字符串）
    :param room_id: 房间ID（字符串）
    :param start_ts: 起始时间戳（整数）
    :param end_ts: 结束时间戳（整数）
    :return: 查询结果列表
    """
    conn = None
    try:
        # 创建数据库连接
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()

        query = sql.SQL("""
            SELECT * FROM {table}
            WHERE room_id = %s
              AND timestamp BETWEEN %s AND %s
        """).format(
            table=sql.Identifier(table_name)# 安全处理表名
        )

        # 执行参数化查询
        cursor.execute(query, (room_id, start_ts, end_ts))
        results = cursor.fetchall()

        return results, cursor.rowcount

    except psycopg2.Error as e:
        print(f"数据库操作失败: {e}")
        return []
    finally:
        if conn:
            conn.close()

# 使用示例
if __name__ == "__main__":
    # 数据库相关
    # 填写你的数据库信息
    db_config = {
        "host": "localhost",
        "database": "postgres",
        "user": "postgres",
        "password": "Zhmz1996Zhmz",
    }

    # 调用查询方法
    data,data_count = query_danmu_by_table_and_room_and_timespan(
        conn_params=db_config,
        table_name="danmu_table",
        room_id="22603245",  # 原字段是varchar类型需保持字符串格式[1](@ref)
        start_ts=1742456400000,
        end_ts=1742456700000
    )

    for row in data:
        print(row)
    print("row_count = {0}".format(data_count))
