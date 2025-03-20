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
sql ="""select * from danmu_table"""
#sql ="""DROP table danmu_table,gift_table,buy_guard_table,user_toast_v2_table,super_chat_table,interact_word_table"""
#danmu_table,gift_table,buy_guard_table,user_toast_v2_table,super_chat_table,interact_word_table

#sql = exist_table_sql
#sql = delete_table_sql
# 动态生成 SQL

# 执行语句
cursor.execute(select_danmu_table_sql)

rows = cursor.fetchall()
print(rows)

count = cursor.rowcount
print(count)


# 事务提交
connection.commit()

# 关闭连接
cursor.close()
connection.close()