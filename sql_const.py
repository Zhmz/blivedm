import psycopg2

exist_table_sql = """SELECT to_regclass(%s) IS NOT NULL AS table_exists;"""

delete_table_sql = """DROP table IF EXISTS %s;"""

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
datatime timestamp
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
datatime
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
%(datatime)s
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
datatime timestamp
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
datatime
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
%(datatime)s
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
datatime timestamp
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
datatime
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
%(datatime)s
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
datatime timestamp
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
datatime
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
%(datatime)s
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

medal_level int,
medal_name text,
medal_room_id bigint,
medal_room_uid bigint,

start_timestamp bigint,
end_timestamp bigint,
datatime timestamp
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

medal_level,
medal_name,
medal_room_id,
medal_room_uid,

start_timestamp,
end_timestamp,
datatime
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

%(medal_level)s,
%(medal_name)s,
%(medal_room_id)s,
%(medal_room_uid)s,

%(start_timestamp)s,
%(end_timestamp)s,
%(datatime)s
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
datatime timestamp
);"""


insert_interact_word_table_sql = """INSERT INTO interact_word_table (
room_id,
user_id,
user_name,
user_face,

msg_type,
msg_text,

timestamp,
datatime
) VALUES (
%(room_id)s,
%(user_id)s,
%(user_name)s,
%(user_face)s,

%(msg_type)s,
%(msg_text)s,

%(timestamp)s,
%(datatime)s
);"""


select_danmu_table_sql = """SELECT * FROM danmu_table
WHERE room_id = '22603245' AND timestamp >= 1742456400000 AND timestamp <= 1742456700000
;"""












