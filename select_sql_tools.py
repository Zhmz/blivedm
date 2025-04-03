import time
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from psycopg2.extras import DictCursor

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

# 根据某天日期查询付费次数和总营收
def query_pay_count_by_room_and_live_date(conn_params, room_id, live_date):
    result = {"gift_table": [],
              "buy_guard_table": [],
              "super_chat_table": []}
    total_count = 0
    total_income = 0

    start_time = time.time()
    try:
        # 创建数据库连接
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                for table in result.keys():
                    query = sql.SQL("""
                        SELECT * FROM {}
                        WHERE room_id = %s
                          AND datetime >= %s::DATE
                          AND datetime < %s::DATE + INTERVAL '1 DAY'
                    """).format(sql.Identifier(table))

                    cursor.execute(query, (str(room_id), live_date, live_date))
                    rows = cursor.fetchall()
                    result[table] = rows
                    total_count += len(rows)

                    if table == 'gift_table':
                        income = sum(
                            (Decimal(str(row['total_coin'])) / Decimal(1000))
                            .quantize(Decimal('0.0'), rounding=ROUND_HALF_UP)
                            for row in rows
                        )
                    elif table == 'buy_guard_table':
                        income = sum(
                            (Decimal(str(row['gift_per_price'])) * Decimal(str(row['gift_num'])) / Decimal(1000))
                            .quantize(Decimal('0.0'), rounding=ROUND_HALF_UP)
                            for row in rows
                        )
                    elif table == 'super_chat_table':
                        income = sum(round(row['price'] * row['gift_num'], 1) for row in rows)
                    total_income += income

                elapsed_ms = (time.time() - start_time) * 1000  # 转为毫秒


    except psycopg2.Error as e:
        print(f"数据库操作失败: {e}")
        return 0, 0, {}, 0
    finally:
        if conn:
            conn.close()

    return total_count, total_income, result, elapsed_ms

# 根据起止时间查询付费次数和总营收
def query_pay_count_by_room_and_live_start_end_time(conn_params, room_id, in_start_time, in_end_time):
    # 需要先去直播状态分钟表里找到直播的上下播具体时间
    # 再把具体时间传入sql里
    result = {"gift_table": [],
              "buy_guard_table": [],
              "super_chat_table": []}
    total_count = 0
    total_income = 0

    start_time = time.time()
    try:
        # 创建数据库连接
        with (psycopg2.connect(**conn_params) as conn):
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                for table in result.keys():
                    # 如果传入的是日期
                    if isinstance(in_start_time, str) and isinstance(in_end_time, str):
                        start_dt = datetime.strptime(in_start_time, "%Y-%m-%d %H:%M:%S")
                        end_dt = datetime.strptime(in_end_time, "%Y-%m-%d %H:%M:%S")
                        query = sql.SQL("""
                            SELECT * FROM {}
                            WHERE room_id = %s
                              AND datetime between %s and %s
                        """).format(sql.Identifier(table))
                        cursor.execute(query, (str(room_id), start_dt, end_dt))
                    else:
                        if table == 'super_chat_table':
                            query = sql.SQL("""
                                SELECT * FROM {}
                                WHERE room_id = %s
                                  AND start_timestamp >= %s and start_timestamp <= %s
                            """).format(sql.Identifier(table))
                        else:
                            query = sql.SQL("""
                                SELECT * FROM {}
                                WHERE room_id = %s
                                  AND timestamp >= %s and timestamp <= %s
                            """).format(sql.Identifier(table))
                        cursor.execute(query, (str(room_id), in_start_time, in_end_time))

                    rows = cursor.fetchall()
                    result[table] = rows
                    total_count += len(rows)

                    if table == 'gift_table':
                        income = sum(
                            (Decimal(str(row['total_coin'])) / Decimal(1000))
                            .quantize(Decimal('0.0'), rounding=ROUND_HALF_UP)
                            for row in rows
                        )
                    elif table == 'buy_guard_table':
                        income = sum(
                            (Decimal(str(row['gift_per_price'])) * Decimal(str(row['gift_num'])) / Decimal(1000))
                            .quantize(Decimal('0.0'), rounding=ROUND_HALF_UP)
                            for row in rows
                        )
                    elif table == 'super_chat_table':
                        income = sum(round(row['price'] * row['gift_num'], 1) for row in rows)
                    total_income += income

                elapsed_ms = (time.time() - start_time) * 1000  # 转为毫秒


    except psycopg2.Error as e:
        print(f"数据库操作失败: {e}")
        return 0, 0, {}, 0
    finally:
        if conn:
            conn.close()

    return total_count, total_income, result, elapsed_ms

# 根据某天日期查询当日直播场次起止时间
def query_live_start_end_time_by_live_date(conn_params, room_id, live_date_str):
    #sql ="""select * from live_status_minute_table WHERE room_id = '7688602' and (live_action = '开始直播' or live_action = '结束直播')"""

    start_ts = 0
    start_time_str = ''
    end_ts = 0
    end_time_str = ''

    start_time = time.time()
    try:
        # 创建数据库连接
        with (psycopg2.connect(**conn_params) as conn):
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                elapsed_ms = (time.time() - start_time) * 1000  # 转为毫秒

                if isinstance(live_date_str, str):
                    live_date_format = datetime.strptime(live_date_str, "%Y-%m-%d")
                query = sql.SQL("""
                                SELECT * FROM live_status_minute_table
                                WHERE room_id = %s
                                AND datetime >= %s::DATE
                                AND datetime < %s::DATE + INTERVAL '1 DAY'
                                AND (live_action = '开始直播' or live_action = '结束直播')
                                """)
                cursor.execute(query, (str(room_id), live_date_format, live_date_format))
                rows = cursor.fetchall()
                for row in rows:
                    print(row)
                    if row['live_status'] == 1 and row['live_action'] == '开始直播':
                        start_ts = row['timestamp']
                        start_time_str = datetime.fromtimestamp(start_ts).strftime('%Y-%m-%d %H:%M:%S')
                    elif (row['live_status'] == 2 or row['live_status'] == 0) and row['live_action'] == '结束直播':
                        end_ts = row['timestamp']
                        end_time_str = datetime.fromtimestamp(end_ts).strftime('%Y-%m-%d %H:%M:%S')
                if start_ts == 0:
                    # 没找到开播时间
                    start_time_str = live_date_format.strftime('%Y-%m-%d %H:%M:%S')
                if end_ts == 0:
                    # 没找到关播时间
                    end_time_str = (live_date_format + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')

    except psycopg2.Error as e:
        print(f"数据库操作失败: {e}")
        return '', '', 0
    finally:
        if conn:
            conn.close()

    return start_time_str, end_time_str, elapsed_ms

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

    # # 礼物
    # data,data_count = query_danmu_by_room_and_timespan(
    #     conn_params=db_config,
    #     room_id="31835822",
    #     start_ts=1742774400000,
    #     end_ts=1742783400000
    # )

    # # 按日期检索付费次数
    # pay_count, total_income, pay_result, execution_time= query_pay_count_by_room_and_live_date(
    #     conn_params=db_config,
    #     room_id="7688602",
    #     live_date='2025-03-29'
    # )
    # 
    # for table, rows in pay_result.items():
    #     print(f"表 {table} 数据：")
    #     for row in rows:
    #         print(row)
    # print(f"总付费次数：{pay_count}，总营收：{total_income}元，总耗时：{execution_time:.2f}ms")

    # 按某天日期查询上下播具体时间
    room_id = "22389206"
    
    start_time_str, end_time_str, execution_time = query_live_start_end_time_by_live_date(
        conn_params=db_config,
        room_id=room_id,
        live_date_str='2025-04-03',
    )

    print(f"start_time_str = {start_time_str}, end_time_str = {end_time_str}, execution_time = {execution_time:.2f}ms")

    # 按场次检索付费次数
    pay_count, total_income, pay_result, execution_time = query_pay_count_by_room_and_live_start_end_time(
        conn_params=db_config,
        room_id=room_id,
        # in_start_time='2025-03-29 10:44:00',
        # in_end_time='2025-03-29 14:13:00'
        # in_start_time=1743216240*1000,
        # in_end_time=1743228780*1000
        in_start_time=start_time_str,
        in_end_time=end_time_str
    )

    for table, rows in pay_result.items():
        print(f"表 {table} 数据：")
        for row in rows:
            print(row)
    print(f"总付费次数：{pay_count}，总营收：{total_income}元，总耗时：{execution_time:.2f}ms")
