import psycopg2

exist_table_sql = """SELECT to_regclass(%s) IS NOT NULL AS table_exists;"""

delete_table_sql = """DROP table IF EXISTS %s;"""

"""基础数据表"""
create_danmu_table_sql = """CREATE TABLE danmu_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
rnd bigint,
dm_type int,
user_id text,
user_name varchar(100),
user_face text,

message text,

vip int,
svip int,
privilege_type int,
medal_level int,
medal_name text,
medal_room_id bigint,
medal_room_name text,

timestamp bigint,
datetime timestamp
);"""

insert_danmu_table_sql = """INSERT INTO danmu_table (
room_id,
rnd,
dm_type,
user_id,
user_name,
user_face,

message,

vip,
svip,
privilege_type,
medal_level,
medal_name,
medal_room_id,
medal_room_name,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(rnd)s,
%(dm_type)s,
%(user_id)s,
%(user_name)s,
%(user_face)s,

%(message)s,

%(vip)s,
%(svip)s,
%(privilege_type)s,
%(medal_level)s,
%(medal_name)s,
%(medal_room_id)s,
%(medal_room_name)s,

%(timestamp)s,
%(datetime)s
);"""


create_gift_table_sql = """CREATE TABLE gift_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
rnd text,
user_id text,
user_name varchar(100),
user_face text,

gift_id int,
gift_type int,
gift_name text,
gift_img_basic text,
gift_action text,
gift_num int,
gift_per_price int,
coin_type text,
total_coin int,

privilege_type int,
medal_level int,
medal_name text,
medal_room_id bigint,
medal_room_uid bigint,

timestamp bigint,
datetime timestamp
);"""


insert_gift_table_sql = """INSERT INTO gift_table (
room_id,
rnd,
user_id,
user_name,
user_face,

gift_id,
gift_type,
gift_name,
gift_img_basic,
gift_action,
gift_num,
gift_per_price,
coin_type,
total_coin,

privilege_type,
medal_level,
medal_name,
medal_room_id,
medal_room_uid,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(rnd)s,
%(user_id)s,
%(user_name)s,
%(user_face)s,

%(gift_id)s,
%(gift_type)s,
%(gift_name)s,
%(gift_img_basic)s,
%(gift_action)s,
%(gift_num)s,
%(gift_per_price)s,
%(coin_type)s,
%(total_coin)s,

%(privilege_type)s,
%(medal_level)s,
%(medal_name)s,
%(medal_room_id)s,
%(medal_room_uid)s,

%(timestamp)s,
%(datetime)s
);"""


create_combo_send_table_sql = """CREATE TABLE combo_send_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
user_id text,
user_name varchar(100),

gift_id int,
gift_name text,
total_num int,

combo_id text,
combo_num int,
combo_total_coin int,
action text,
batch_combo_id text,
batch_combo_num int,

r_uid bigint,
r_uname text,

timestamp bigint,
datetime timestamp
);"""


insert_combo_send_table_sql = """INSERT INTO combo_send_table (
room_id,
user_id,
user_name,

gift_id,
gift_name,
total_num,

combo_id,
combo_num,
combo_total_coin,
action,
batch_combo_id,
batch_combo_num,

r_uid,
r_uname,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(user_id)s,
%(user_name)s,

%(gift_id)s,
%(gift_name)s,
%(total_num)s,

%(combo_id)s,
%(combo_num)s,
%(combo_total_coin)s,
%(action)s,
%(batch_combo_id)s,
%(batch_combo_num)s,

%(r_uid)s,
%(r_uname)s,

%(timestamp)s,
%(datetime)s
);"""


create_buy_guard_table_sql = """CREATE TABLE buy_guard_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
user_id text,
user_name varchar(100),
privilege_type int,

gift_id int,
gift_name text,
gift_num int,
gift_per_price int,

timestamp bigint,
datetime timestamp
);"""


insert_buy_guard_table_sql = """INSERT INTO buy_guard_table (
room_id,
user_id,
user_name,
privilege_type,

gift_id,
gift_name,
gift_num,
gift_per_price,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(user_id)s,
%(user_name)s,
%(privilege_type)s,

%(gift_id)s,
%(gift_name)s,
%(gift_num)s,
%(gift_per_price)s,

%(timestamp)s,
%(datetime)s
);"""


create_user_toast_v2_table_sql = """CREATE TABLE user_toast_v2_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
user_id text,
user_name varchar(100),
privilege_type int,

gift_id int,
gift_num int,
gift_per_price int,
gift_unit text,
source int,
toast_msg text,

timestamp bigint,
datetime timestamp
);"""


insert_user_toast_v2_table_sql = """INSERT INTO user_toast_v2_table (
room_id,
user_id,
user_name,
privilege_type,

gift_id,
gift_num,
gift_per_price,
gift_unit,
source,
toast_msg,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(user_id)s,
%(user_name)s,
%(privilege_type)s,

%(gift_id)s,
%(gift_num)s,
%(gift_per_price)s,
%(gift_unit)s,
%(source)s,
%(toast_msg)s,

%(timestamp)s,
%(datetime)s
);"""


create_super_chat_table_sql = """CREATE TABLE super_chat_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
user_id text,
user_name varchar(100),
user_face text,
user_level int,
privilege_type int,

super_chat_id int,
price int,
super_chat_msg text,
available_timestamp int,
gift_id int,
gift_name text,
gift_num int,

medal_level int,
medal_name text,
medal_room_id bigint,
medal_room_uid bigint,

start_timestamp bigint,
end_timestamp bigint,
datetime timestamp
);"""


insert_super_chat_table_sql = """INSERT INTO super_chat_table (
room_id,
user_id,
user_name,
user_face,
user_level,
privilege_type,

super_chat_id,
price,
super_chat_msg,
available_timestamp,
gift_id,
gift_name,
gift_num,

medal_level,
medal_name,
medal_room_id,
medal_room_uid,

start_timestamp,
end_timestamp,
datetime
) VALUES (
%(room_id)s,
%(user_id)s,
%(user_name)s,
%(user_face)s,
%(user_level)s,
%(privilege_type)s,

%(super_chat_id)s,
%(price)s,
%(super_chat_msg)s,
%(available_timestamp)s,
%(gift_id)s,
%(gift_name)s,
%(gift_num)s,

%(medal_level)s,
%(medal_name)s,
%(medal_room_id)s,
%(medal_room_uid)s,

%(start_timestamp)s,
%(end_timestamp)s,
%(datetime)s
);"""


create_interact_word_table_sql = """CREATE TABLE interact_word_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
user_id text,
user_name varchar(100),
user_face text,

msg_type int,
msg_text text,

timestamp bigint,
datetime timestamp
);"""


insert_interact_word_table_sql = """INSERT INTO interact_word_table (
room_id,
user_id,
user_name,
user_face,

msg_type,
msg_text,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(user_id)s,
%(user_name)s,
%(user_face)s,

%(msg_type)s,
%(msg_text)s,

%(timestamp)s,
%(datetime)s
);"""


# 看过人次表
create_watch_change_table_sql = """CREATE TABLE watch_change_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
count int,

timestamp bigint,
datetime timestamp
);"""


insert_watch_change_table_sql = """INSERT INTO watch_change_table (
room_id,
count,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(count)s,

%(timestamp)s,
%(datetime)s
);"""


# 点赞表
create_like_info_update_table_sql = """CREATE TABLE like_info_update_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
count int,

timestamp bigint,
datetime timestamp
);"""


insert_like_info_update_table_sql = """INSERT INTO like_info_update_table (
room_id,
count,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(count)s,

%(timestamp)s,
%(datetime)s
);"""


"""分钟表"""
# 付费榜人数分钟表
create_online_rank_count_minute_table_sql = """CREATE TABLE online_rank_count_minute_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
count int,

timestamp bigint,
datetime timestamp
);"""


insert_online_rank_count_minute_table_sql = """INSERT INTO online_rank_count_minute_table (
room_id,
count,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(count)s,

%(timestamp)s,
%(datetime)s
);"""


# 互动次数分钟表
create_interact_word_count_minute_table_sql = """CREATE TABLE interact_word_count_minute_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
count int,

timestamp bigint,
datetime timestamp
);"""


insert_interact_word_count_minute_table_sql = """INSERT INTO interact_word_count_minute_table (
room_id,
count,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(count)s,

%(timestamp)s,
%(datetime)s
);"""


# 进入房间人次分钟表
create_enter_room_count_minute_table_sql = """CREATE TABLE enter_room_count_minute_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
count int,

timestamp bigint,
datetime timestamp
);"""


insert_enter_room_count_minute_table_sql = """INSERT INTO enter_room_count_minute_table (
room_id,
count,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(count)s,

%(timestamp)s,
%(datetime)s
);"""


# 弹幕数量分钟表
create_danmu_count_minute_table_sql = """CREATE TABLE danmu_count_minute_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
count int,

timestamp bigint,
datetime timestamp
);"""


insert_danmu_count_minute_table_sql = """INSERT INTO danmu_count_minute_table (
room_id,
count,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(count)s,

%(timestamp)s,
%(datetime)s
);"""


# 营收分钟表
create_income_minute_table_sql = """CREATE TABLE income_minute_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
income float,

timestamp bigint,
datetime timestamp
);"""


insert_income_minute_table_sql = """INSERT INTO income_minute_table (
room_id,
income,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(income)s,

%(timestamp)s,
%(datetime)s
);"""


#直播状态分钟表
create_live_status_minute_table_sql = """CREATE TABLE live_status_minute_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
live_status int,
live_action text,

timestamp bigint,
datetime timestamp
);"""


insert_live_status_minute_table_sql = """INSERT INTO live_status_minute_table (
room_id,
live_status,
live_action,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(live_status)s,
%(live_action)s,

%(timestamp)s,
%(datetime)s
);"""


"""场次表"""
# # 场次付费次数表
# create_pay_count_live_table_sql = """CREATE TABLE pay_count_live_table (
# id serial4 PRIMARY KEY,
# 
# room_id varchar(10),
# start_time_str text,
# end_time_str text,
# pay_count int,
# 
# timestamp bigint,
# datetime timestamp
# );"""
# 
# 
# insert_pay_count_live_table_sql = """INSERT INTO pay_count_live_table (
# room_id,
# start_time_str,
# end_time_str,
# pay_count,
# 
# timestamp,
# datetime
# ) VALUES (
# %(room_id)s,
# %(start_time_str)s,
# %(end_time_str)s,
# %(pay_count)s,
# 
# %(timestamp)s,
# %(datetime)s
# );"""

# 场次营收表
create_income_live_table_sql = """CREATE TABLE income_live_table (
id serial4 PRIMARY KEY,

room_id varchar(10),
start_time_str text,
end_time_str text,

pay_count int,
income float,
watch_change_count int,
like_info_update_count int,

timestamp bigint,
datetime timestamp
);"""


insert_income_live_table_sql = """INSERT INTO income_live_table (
room_id,
start_time_str,
end_time_str,

pay_count,
income,
watch_change_count,
like_info_update_count,

timestamp,
datetime
) VALUES (
%(room_id)s,
%(start_time_str)s,
%(end_time_str)s,

%(pay_count)s,
%(income)s,
%(watch_change_count)s,
%(like_info_update_count)s,

%(timestamp)s,
%(datetime)s
);"""








