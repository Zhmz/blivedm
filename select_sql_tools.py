import copy
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


def query_live_start_time_by_end_time(conn_params, room_id, end_time_str):
    start_time_str = ''
    end_time_format = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

    execution_start_time = time.time()
    try:
        # 创建数据库连接
        with (psycopg2.connect(**conn_params) as conn):
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                query = sql.SQL("""
                                SELECT * FROM live_status_minute_table
                                WHERE room_id = %s
                                AND datetime >= %s - INTERVAL '24 HOURS'
                                AND datetime < %s
                                AND live_action = '开始直播'
                                ORDER BY datetime DESC
                                LIMIT 1
                                """)
                cursor.execute(query, (str(room_id), end_time_format, end_time_format))
                result_rows = cursor.fetchall()
                if len(result_rows) > 0:
                    start_minute_data = result_rows[0]# 只返回一条数据
                    start_time_str = datetime.fromtimestamp(start_minute_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    cur_day_zero_time = end_time_format.replace(hour=0, minute=0, second=0, microsecond=0)
                    start_time_str = cur_day_zero_time.strftime('%Y-%m-%d %H:%M:%S')
                elapsed_ms = (time.time() - execution_start_time) * 1000  # 转为毫秒
    except psycopg2.Error as e:
        print(f"数据库操作失败: {e}")
        return '', 0
    finally:
        if conn:
            conn.close()
    return start_time_str, elapsed_ms

# 根据某天日期查询当日直播场次起止时间
# date_is_start_live_date 传入的日期是开播时间所在的日期
def query_live_start_end_time_by_live_date(conn_params, room_id, live_date_str, date_is_start_live_date=False):
    start_ts = 0
    start_time_str = ''
    end_ts = 0
    end_time_str = ''

    # 里面是每一组开播和关播的字典
    result_time_pair_list = []
    temp_live_time_pair = {}

    start_time = time.time()
    try:
        # 创建数据库连接
        with (psycopg2.connect(**conn_params) as conn):
            with conn.cursor(cursor_factory=DictCursor) as cursor:

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

                # 从0点开始往下找开播或关播时间
                for row in rows:
                    # print(row)
                    if row['live_status'] == 1 and row['live_action'] == '开始直播':
                        start_time_str = datetime.fromtimestamp(row['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                        temp_live_time_pair['start_time_str'] = start_time_str
                    elif (row['live_status'] == 2 or row['live_status'] == 0) and row['live_action'] == '结束直播':
                        end_time_str = datetime.fromtimestamp(row['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                        temp_live_time_pair['end_time_str'] = end_time_str

                        # 如果传入的是关播日期，才可能需要往前一天找开播时间
                        if not date_is_start_live_date:
                            # 如果 temp_live_time_pair 没有 key == 'start_time_str'，说明这是跨天直播，需要到前一天去找关播时间
                            # 找到后，将开播时间加入到temp_live_time_pair
                            if 'start_time_str' not in temp_live_time_pair.keys():
                                prev_live_date_str = (live_date_format - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                                cursor.execute(query, (str(room_id), prev_live_date_str, prev_live_date_str))
                                prev_rows = cursor.fetchall()
                                if len(prev_rows) == 0:
                                    print(f"结束直播时间 {end_time_str} 无法匹配到前一天的 开始直播时间。")
                                else:
                                    last_prev_row = prev_rows[-1]
                                    if last_prev_row['live_status'] == 1 and last_prev_row['live_action'] == '开始直播':
                                        prev_start_ts = last_prev_row['timestamp']
                                        prev_start_time_str = datetime.fromtimestamp(prev_start_ts).strftime(
                                            '%Y-%m-%d %H:%M:%S')
                                        temp_live_time_pair['start_time_str'] = prev_start_time_str

                        # 已有当天的开播时间 或者 前一天找到开播时间，需要把pair放入list
                        if 'start_time_str' in temp_live_time_pair.keys():
                            to_append_pair = copy.deepcopy(temp_live_time_pair)
                            result_time_pair_list.append(to_append_pair)
                        # 不管是否找到，都需要清空 temp_live_time_pair
                        temp_live_time_pair = {}

                # 1. 如果传入的是开播日期
                # 2. 且最后一个元素是开播，则说明当天缺少结束直播时间，需要去下一天找结束直播时间
                if date_is_start_live_date:
                    last_row = rows[-1]
                    last_start_time_str = datetime.fromtimestamp(last_row['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                    if last_row['live_status'] == 1 and last_row['live_action'] == '开始直播':
                        next_live_date_str = (live_date_format + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute(query, (str(room_id), next_live_date_str, next_live_date_str))
                        next_rows = cursor.fetchall()
                        if len(next_rows) == 0:
                            print(f"开始直播时间 {last_start_time_str} 无法匹配到后一天的 结束直播时间。")
                        else:
                            first_next_row = next_rows[0]
                            if (first_next_row['live_status'] == 2 or first_next_row['live_status'] == 0) and first_next_row['live_action'] == '结束直播':
                                next_end_ts = first_next_row['timestamp']
                                next_end_time_str = datetime.fromtimestamp(next_end_ts).strftime('%Y-%m-%d %H:%M:%S')

                                # 找到下一日的结束时间，将这一组数据加入result
                                temp_live_time_pair['end_time_str'] = next_end_time_str
                                temp_live_time_pair['start_time_str'] = last_start_time_str
                                to_append_pair = copy.deepcopy(temp_live_time_pair)
                                result_time_pair_list.append(to_append_pair)
                
                elapsed_ms = (time.time() - start_time) * 1000  # 转为毫秒
    except psycopg2.Error as e:
        print(f"数据库操作失败: {e}")
        return result_time_pair_list, 0
    finally:
        if conn:
            conn.close()

    return result_time_pair_list, elapsed_ms


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

    # # 按某天日期查询上下播具体时间
    # room_id = "22603245"
    # is_start_live_date = False
    # live_date_str = '2025-04-10'
    # pair_list, execution_time = query_live_start_end_time_by_live_date(
    #     conn_params=db_config,
    #     room_id=room_id,
    #     live_date_str=live_date_str,
    #     date_is_start_live_date=is_start_live_date
    # )
    # 
    # print(f"execution_time = {execution_time:.2f}ms")
    # title_str = "开" if is_start_live_date else "关"
    # title_str += f"播日期为 {live_date_str} 的直播共 {len(pair_list)} 场"
    # if len(pair_list) > 0:
    #     title_str += "，时间如下："
    # print(title_str)
    # for i in range(len(pair_list)):
    #     pair = pair_list[i]
    #     start_time = pair['start_time_str']
    #     end_time = pair['end_time_str']
    #     print(f"第 {i + 1} 场直播：开始时间 = {start_time}, 结束时间 = {end_time}")
    # 
    #     # 按场次检索付费次数
    #     pay_count, total_income, pay_result, execution_time = query_pay_count_by_room_and_live_start_end_time(
    #         conn_params=db_config,
    #         room_id=room_id,
    #         # in_start_time='2025-03-29 10:44:00',
    #         # in_end_time='2025-03-29 14:13:00'
    #         # in_start_time=1743216240*1000,
    #         # in_end_time=1743228780*1000
    #         in_start_time=start_time,
    #         in_end_time=end_time
    #     )
    # 
    #     # for table, rows in pay_result.items():
    #     #     print(f"表 {table} 数据：")
    #     #     for row in rows:
    #     #         print(row)
    #     print(f"总付费次数：{pay_count}，总营收：{total_income}元，总耗时：{execution_time:.2f}ms")


    # # 按场次检索付费次数
    # room_id = "10055155"
    # pay_count, total_income, pay_result, execution_time = query_pay_count_by_room_and_live_start_end_time(
    #     conn_params=db_config,
    #     room_id=room_id,
    #     in_start_time='2025-04-11 18:00:00',
    #     in_end_time='2025-04-14 00:00:00'
    #     # in_start_time=1743216240*1000,
    #     # in_end_time=1743228780*1000
    #     # in_start_time=start_time,
    #     # in_end_time=end_time
    # )
    # 
    # for table, rows in pay_result.items():
    #     print(f"表 {table} 数据：")
    #     for row in rows:
    #         print(row)
    # print(f"总付费次数：{pay_count}，总营收：{total_income}元，总耗时：{execution_time:.2f}ms")

    # 给一个时间找最接近的开播时间
    room_id = "22992234"
    start_time_str, execution_time = query_live_start_time_by_end_time(
        conn_params=db_config,
        room_id=room_id,
        end_time_str='2025-04-14 14:48:00'
    )

    print(f"上一次开播时间：{start_time_str}，总耗时：{execution_time:.2f}ms")
