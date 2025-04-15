from datetime import datetime, time
import time

from select_sql_tools import query_live_start_end_time_by_live_date, query_pay_count_by_room_and_live_start_end_time, \
    query_live_start_time_by_end_time

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
    room_id = "24692760"
    is_start_live_date = False
    live_date_str = '2025-04-14'
    pair_list, execution_time = query_live_start_end_time_by_live_date(
        conn_params=db_config,
        room_id=room_id,
        live_date_str=live_date_str,
        date_is_start_live_date=is_start_live_date
    )

    print(f"execution_time = {execution_time:.2f}ms")
    title_str = "开" if is_start_live_date else "关"
    title_str += f"播日期为 {live_date_str} 的直播共 {len(pair_list)} 场"
    if len(pair_list) > 0:
        title_str += "，时间如下："
    print(title_str)
    for i in range(len(pair_list)):
        pair = pair_list[i]
        start_time = pair['start_time_str']
        end_time = pair['end_time_str']
        print(f"第 {i + 1} 场直播：开始时间 = {start_time}, 结束时间 = {end_time}")

        # 按场次检索付费次数
        pay_count, total_income, pay_result, execution_time = query_pay_count_by_room_and_live_start_end_time(
            conn_params=db_config,
            room_id=room_id,
            # in_start_time='2025-03-29 10:44:00',
            # in_end_time='2025-03-29 14:13:00'
            # in_start_time=1743216240*1000,
            # in_end_time=1743228780*1000
            in_start_time=start_time,
            in_end_time=end_time
        )

        # for table, rows in pay_result.items():
        #     print(f"表 {table} 数据：")
        #     for row in rows:
        #         print(row)
        print(f"总付费次数：{pay_count}，总营收：{total_income}元，总耗时：{execution_time:.2f}ms")


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
    room_id = "24692760"
    cur_timestamp = int(round(time.time()))#单位：秒
    cur_dt = datetime.fromtimestamp(cur_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    start_time_str, execution_time = query_live_start_time_by_end_time(
        conn_params=db_config,
        room_id=room_id,
        end_time_str=cur_dt
    )

    print(f"上一次开播时间：{start_time_str}，总耗时：{execution_time:.2f}ms")