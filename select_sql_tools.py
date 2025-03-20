from sql_const import *
import psycopg2
from psycopg2 import sql


def query_danmu_by_room_and_timespan(conn_params, room_id, start_ts, end_ts):
    conn = None
    try:
        # 创建数据库连接
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()

        query = sql.SQL("""
            SELECT * FROM danmu_table
            WHERE room_id = %s
              AND timestamp BETWEEN %s AND %s
        """)

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



def query_gift_by_room_and_timespan(conn_params, room_id, start_ts, end_ts):
    conn = None
    try:
        # 创建数据库连接
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()

        query = sql.SQL("""
            SELECT * FROM gift_table
            WHERE room_id = %s
              AND timestamp BETWEEN %s AND %s
        """)

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

    # # 弹幕
    # data,data_count = query_danmu_by_room_and_timespan(
    #     conn_params=db_config,
    #     room_id="80397",
    #     start_ts=1742460600000,
    #     end_ts=1742460900000
    # )

    # 礼物
    data,data_count = query_gift_by_room_and_timespan(
        conn_params=db_config,
        room_id="22603245",
        start_ts=1742455800000,
        end_ts=1742460900000
    )


    for row in data:
        print(row)
    print("row_count = {0}".format(data_count))
