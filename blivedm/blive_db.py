import psycopg2
from psycopg2 import sql

from sql_const import *

# 填写你的数据库信息
db_config = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "Zhmz1996Zhmz",
}

# 连接到 PostgreSQL 数据库
connection = psycopg2.connect(**db_config)

# 创建一个游标对象
cursor = connection.cursor()

#sql语句，建表
sql ="""select * from live_status_minute_table WHERE room_id = '21652717'"""
#sql ="""DROP table live_status_minute_table"""
#danmu_table,gift_table,buy_guard_table,user_toast_v2_table,super_chat_table,interact_word_table
#online_rank_count_minute_table,interact_word_count_minute_table,enter_room_count_minute_table,income_minute_table,live_status_minute_table

#还没创建的场次表
#watch_change_table,like_info_update_table

# 动态生成 SQL

# 执行语句
cursor.execute(sql)

rows = cursor.fetchall()
print(rows)

count = cursor.rowcount
print(count)


# 事务提交
connection.commit()

# 关闭连接
cursor.close()
connection.close()