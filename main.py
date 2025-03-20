# -*- coding: utf-8 -*-
import asyncio
import copy
import http.cookies
import random
from datetime import datetime
from typing import *

import aiohttp
from psycopg2 import OperationalError

import blivedm
import blivedm.models.web as web_models
import json
from pathlib import Path

import psycopg2

from sql_const import *

# 直播间ID的取值看直播间URL
TEST_ROOM_IDS = [
    # 7734200,#哔哩哔哩英雄联盟赛事
    22603245,#永雏塔菲
    # 22389206,#折原露露
    # 27183290,#雪糕cheese
    # 31835822,#萝尔露Real
    # 7688602,#花花Haya
    # 22816111,#东雪莲
    # 21652717,#白神遥
    # 22992234,#蕾尔娜Leona
    80397,#阿梓
    # 22333522,#伊万
]

# 数据库相关
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

def table_exists(table_name, schema_name='public'):
    full_table_name = f"{schema_name}.{table_name}"
    try:
        cursor.execute(exist_table_sql, (full_table_name,))
        result = cursor.fetchone()
        return result[0] if result else False
    except OperationalError as e:
        print(f"数据库连接失败: {e}")
        return False

# 创建danmu表
if not table_exists("danmu_table"):
    cursor.execute(create_danmu_table_sql)
    print("danmu_table created successfully")
if not table_exists("gift_table"):
    cursor.execute(create_gift_table_sql)
    print("gift_table created successfully")
if not table_exists("buy_guard_table"):
    cursor.execute(create_buy_guard_table_sql)
    print("buy_guard_table created successfully")
if not table_exists("user_toast_v2_table"):
    cursor.execute(create_user_toast_v2_table_sql)
    print("user_toast_v2_table created successfully")
if not table_exists("super_chat_table"):
    cursor.execute(create_super_chat_table_sql)
    print("super_chat_table created successfully")
if not table_exists("interact_word_table"):
    cursor.execute(create_interact_word_table_sql)
    print("interact_word_table created successfully")
connection.commit()

# 这里填一个已登录账号的cookie的SESSDATA字段的值。不填也可以连接，但是收到弹幕的用户名会打码，UID会变成0
SESSDATA = '860abe6c%2C1757991352%2C6ab50%2A31CjBB6BCoJjckpe20ZeNG5Nf4kpLJ7WsN1ikJZzYZU0F_IpoWhOtRE0_bnFrMZUhE1hYSVldZYmRVSVBjNFpRX00yczJLVXBZZW55NHJSSWc2LUxRLXlDTHRPaU9jWG9oX2tnQ0VNVnljaHNwTW5OLUVPUmtPcWFwaVVWSXQyYjBqSUFkdEMtS2lRIIEC'

session: Optional[aiohttp.ClientSession] = None

async def main():
    init_session()
    try:
        await run_single_client()
        await run_multi_clients()
    finally:
        await session.close()
    # TODO: 数据库关闭


def init_session():
    cookies = http.cookies.SimpleCookie()
    cookies['SESSDATA'] = SESSDATA
    cookies['SESSDATA']['domain'] = 'bilibili.com'

    global session
    session = aiohttp.ClientSession()
    session.cookie_jar.update_cookies(cookies)


async def run_single_client():
    """
    演示监听一个直播间
    """
    room_id = random.choice(TEST_ROOM_IDS)
    client = blivedm.BLiveClient(room_id, session=session)
    handler = MyHandler()
    client.set_handler(handler)

    client.start()
    try:
        # 演示5秒后停止
        await asyncio.sleep(5)
        client.stop()

        await client.join()
    finally:
        await client.stop_and_close()


async def run_multi_clients():
    """
    演示同时监听多个直播间
    """
    clients = [blivedm.BLiveClient(room_id, session=session) for room_id in TEST_ROOM_IDS]
    handler = MyHandler()
    for client in clients:
        client.set_handler(handler)
        client.start()

    try:
        await asyncio.gather(*(
            client.join() for client in clients
        ))
    finally:
        await asyncio.gather(*(
            client.stop_and_close() for client in clients
        ))


class MyHandler(blivedm.BaseHandler):
    # # 演示如何添加自定义回调
    # _CMD_CALLBACK_DICT = blivedm.BaseHandler._CMD_CALLBACK_DICT.copy()
    #
    # # 看过数消息回调
    # def __watched_change_callback(self, client: blivedm.BLiveClient, command: dict):
    #     print(f'[{client.room_id}] WATCHED_CHANGE: {command}')
    # _CMD_CALLBACK_DICT['WATCHED_CHANGE'] = __watched_change_callback  # noqa

    # db存入计数器
    danmu_db_index = 0
    gift_db_index = 0
    buy_guard_db_index = 0
    user_toast_v2_db_index = 0
    super_chat_db_index = 0
    interact_word_db_index = 0

    # 写入数据库的池子的阈值
    danmu_db_threshold = 10
    gift_db_threshold = 10
    buy_guard_db_threshold = 10
    user_toast_v2_db_threshold = 10
    super_chat_db_threshold = 10
    interact_word_db_threshold = 10

    # db数据对象池
    danmu_pool = []
    danmu_commit_pool = []
    gift_pool = []
    gift_commit_pool = []
    buy_guard_pool = []
    buy_guard_commit_pool = []
    user_toast_v2_pool = []
    user_toast_v2_commit_pool = []
    super_chat_pool = []
    super_chat_commit_pool = []
    interact_word_pool = []
    interact_word_commit_pool = []


    def _on_heartbeat(self, client: blivedm.BLiveClient, message: web_models.HeartbeatMessage):
        print(f'[{client.room_id}] 心跳')

    def _on_danmaku(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        seconds = message.timestamp / 1000
        dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{client.room_id}] [{dt}] {message.uname}：{message.msg}')


        params = {'room_id': client.room_id,
                  'rnd': message.rnd,
                  'dm_type': message.dm_type,
                  'user_id': message.uid,
                  'user_name': message.uname,
                  'user_face': message.face,
                  'message': message.msg,

                  'vip': message.vip,
                  'svip': message.svip,
                  'privilege_type': message.privilege_type,
                  'medal_level': message.medal_level,
                  'medal_name': message.medal_name,
                  'medal_room_id': message.medal_room_id,
                  'medal_room_name': message.runame,

                  'timestamp': message.timestamp,
                  'datatime': dt
                  }

        # 存入对象池
        self.danmu_pool.append(params)
        self.danmu_db_index += 1
        if self.danmu_db_index >= self.danmu_db_threshold:
            self.danmu_commit_pool = copy.deepcopy(self.danmu_pool)
            self.danmu_pool = []

            print("insert danmu successfully,count = "+str(self.danmu_db_index)+", pool count = "+str(len(self.danmu_commit_pool)))
            self.danmu_db_index = 0
            cursor.executemany(insert_danmu_table_sql, self.danmu_commit_pool)
            connection.commit()

    def _on_gift(self, client: blivedm.BLiveClient, message: web_models.GiftMessage):
        seconds = message.timestamp / 1000
        dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{client.room_id}] [{dt}] {message.uname} 赠送{message.gift_name}x{message.num}'
              f' （{message.coin_type}瓜子x{message.total_coin}）')

        params = {'room_id': client.room_id,
                  'rnd': message.rnd,
                  'user_id': message.uid,
                  'user_name': message.uname,
                  'user_face': message.face,

                  'gift_id': message.gift_id,
                  'gift_type': message.gift_type,
                  'gift_name': message.gift_name,
                  'gift_img_basic': message.gift_img_basic,
                  'gift_action': message.action,
                  'gift_num': message.num,
                  'gift_per_price': message.price,
                  'coin_type': message.coin_type,
                  'total_coin': message.total_coin,

                  'privilege_type': message.guard_level,
                  'medal_level': message.medal_level,
                  'medal_name': message.medal_name,
                  'medal_room_id': message.medal_room_id,
                  'medal_room_uid': message.medal_ruid,

                  'timestamp': message.timestamp,
                  'datatime': dt
                  }

        # 存入对象池
        self.gift_pool.append(params)
        self.gift_db_index += 1
        if self.gift_db_index >= self.gift_db_threshold:
            self.gift_commit_pool = copy.deepcopy(self.gift_pool)
            self.gift_pool = []

            print("insert gift successfully,count = "+str(self.gift_db_index)+", pool count = "+str(len(self.gift_commit_pool)))
            self.gift_db_index = 0
            cursor.executemany(insert_gift_table_sql, self.gift_commit_pool)
            connection.commit()

    def _on_buy_guard(self, client: blivedm.BLiveClient, message: web_models.GuardBuyMessage):
        seconds = message.start_time / 1000
        dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{client.room_id}] [{dt}] {message.username} 上舰，guard_level={message.guard_level}')

        params = {'room_id': client.room_id,
                  'user_id': message.uid,
                  'user_name': message.username,
                  'privilege_type': message.guard_level,

                  'gift_id': message.gift_id,
                  'gift_name': message.gift_name,
                  'gift_num': message.num,
                  'gift_per_price': message.price,

                  'timestamp': message.start_time,
                  'datatime': dt
                  }

        # 存入对象池
        self.buy_guard_pool.append(params)
        self.buy_guard_db_index += 1
        if self.buy_guard_db_index >= self.buy_guard_db_threshold:
            self.buy_guard_commit_pool = copy.deepcopy(self.buy_guard_pool)
            self.buy_guard_pool = []

            print("insert buy_guard successfully,count = "+str(self.buy_guard_db_index)+", pool count = "+str(len(self.buy_guard_commit_pool)))
            self.buy_guard_db_index = 0
            cursor.executemany(insert_buy_guard_table_sql, self.buy_guard_commit_pool)
            connection.commit()

    def _on_user_toast_v2(self, client: blivedm.BLiveClient, message: web_models.UserToastV2Message):
        seconds = message.start_time / 1000
        dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{client.room_id}] [{dt}] {message.username} 上舰，guard_level={message.guard_level}')

        params = {'room_id': client.room_id,
                  'user_id': message.uid,
                  'user_name': message.username,
                  'privilege_type': message.guard_level,

                  'gift_id': message.gift_id,
                  'gift_num': message.num,
                  'gift_per_price': message.price,
                  'gift_unit': message.unit,
                  'source': message.source,
                  'toast_msg': message.toast_msg,

                  'timestamp': message.start_time,
                  'datatime': dt
                  }

        # 存入对象池
        self.user_toast_v2_pool.append(params)
        self.user_toast_v2_db_index += 1
        if self.user_toast_v2_db_index >= self.user_toast_v2_db_threshold:
            self.user_toast_v2_commit_pool = copy.deepcopy(self.user_toast_v2_pool)
            self.user_toast_v2_pool = []

            print("insert user_toast_v2 successfully,count = "+str(self.user_toast_v2_db_index)+", pool count = "+str(len(self.user_toast_v2_commit_pool)))
            self.user_toast_v2_db_index = 0
            cursor.executemany(insert_user_toast_v2_table_sql, self.user_toast_v2_commit_pool)
            connection.commit()

    def _on_super_chat(self, client: blivedm.BLiveClient, message: web_models.SuperChatMessage):
        seconds = message.start_time / 1000
        dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{client.room_id}] [{dt}] 醒目留言 ¥{message.price} {message.uname}：{message.message}')

        params = {'room_id': client.room_id,
                  'user_id': message.uid,
                  'user_name': message.uname,
                  'user_face': message.face,
                  'user_level': message.user_level,
                  'privilege_type': message.guard_level,

                  'super_chat_id': message.id,
                  'price': message.price,
                  'super_chat_msg': message.message,
                  'available_timestamp': message.time,
                  'gift_id': message.gift_id,
                  'gift_name': message.gift_name,

                  'medal_level': message.medal_level,
                  'medal_name': message.medal_name,
                  'medal_room_id': message.medal_room_id,
                  'medal_room_uid': message.medal_ruid,

                  'start_timestamp': message.start_time,
                  'end_timestamp': message.end_time,
                  'datatime': dt
                  }

        # 存入对象池
        self.super_chat_pool.append(params)
        self.super_chat_db_index += 1
        if self.super_chat_db_index >= self.super_chat_db_threshold:
            self.super_chat_commit_pool = copy.deepcopy(self.super_chat_pool)
            self.super_chat_pool = []

            print("insert super_chat successfully,count = "+str(self.super_chat_db_index)+", pool count = "+str(len(self.super_chat_commit_pool)))
            self.super_chat_db_index = 0
            cursor.executemany(insert_super_chat_table_sql, self.super_chat_commit_pool)
            connection.commit()

    def _on_interact_word(self, client: blivedm.BLiveClient, message: web_models.InteractWordMessage):
        seconds = message.timestamp / 1000
        dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')

        temp_interact_word = {}

        # if message.msg_type == 1:
        #     # 这个太多了，先屏蔽一下
        #     print(f'[{client.room_id}] [{dt}] {message.username} 进入房间')
        if message.msg_type == 2:
            print(f'[{client.room_id}] [{dt}] {message.username} 关注了主播')
            temp_interact_word["action"] = "关注了主播"
        elif message.msg_type == 3:
            print(f'[{client.room_id}] [{dt}] {message.username} 分享了房间')
            temp_interact_word["action"] = "分享了房间"
        elif message.msg_type == 4:
            print(f'[{client.room_id}] [{dt}] {message.username} 特别关注了主播')
            temp_interact_word["action"] = "特别关注了主播"
        elif message.msg_type == 5:
            print(f'[{client.room_id}] [{dt}] {message.username} 与主播互粉了')
            temp_interact_word["action"] = "与主播互粉了"
        elif message.msg_type == 6:
            print(f'[{client.room_id}] [{dt}] {message.username} 为主播点赞了')
            temp_interact_word["action"] = "为主播点赞了"

        # 进入房间，这个不打印
        if message.msg_type != 1:
            params = {'room_id': client.room_id,
                      'user_id': message.uid,
                      'user_name': message.username,
                      'user_face': message.face,

                      'msg_type': message.msg_type,
                      'msg_text': temp_interact_word["action"],

                      'timestamp': message.timestamp,
                      'datatime': dt
                      }

            # 存入对象池
            self.interact_word_pool.append(params)
            self.interact_word_db_index += 1
            if self.interact_word_db_index >= self.interact_word_db_threshold:
                self.interact_word_commit_pool = copy.deepcopy(self.interact_word_pool)
                self.interact_word_pool = []

                print("insert interact_word successfully,count = "+str(self.interact_word_db_index)+", pool count = "+str(len(self.interact_word_commit_pool)))
                self.interact_word_db_index = 0
                cursor.executemany(insert_interact_word_table_sql, self.interact_word_commit_pool)
                connection.commit()

if __name__ == '__main__':
    asyncio.run(main())
