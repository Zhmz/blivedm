# -*- coding: utf-8 -*-
import asyncio
import copy
import http.cookies
import math
import random
from datetime import datetime, time
import time
from typing import *

import aiohttp
from psycopg2 import OperationalError
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import blivedm
import blivedm.models.web as web_models
import blivedm.models.open_live as open_models
import json
from pathlib import Path
import requests

import psycopg2

from blive_const import TEST_ROOM_IDS, SESSDATA, BUVID3
from select_sql_tools import query_live_start_end_time_by_live_date, query_pay_count_by_room_and_live_start_end_time
from sql_const import *



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
if not table_exists("combo_send_table"):
    cursor.execute(create_combo_send_table_sql)
    print("combo_send_table created successfully")
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
if not table_exists("watch_change_table"):
    cursor.execute(create_watch_change_table_sql)
    print("watch_change_table created successfully")
if not table_exists("like_info_update_table"):
    cursor.execute(create_like_info_update_table_sql)
    print("like_info_update_table created successfully")

# 创建分钟表
if not table_exists("online_rank_count_minute_table"):
    cursor.execute(create_online_rank_count_minute_table_sql)
    print("online_rank_count_minute_table created successfully")
if not table_exists("interact_word_count_minute_table"):
    cursor.execute(create_interact_word_count_minute_table_sql)
    print("interact_word_count_minute_table created successfully")
if not table_exists("enter_room_count_minute_table"):
    cursor.execute(create_enter_room_count_minute_table_sql)
    print("enter_room_count_minute_table created successfully")
if not table_exists("danmu_count_minute_table"):
    cursor.execute(create_danmu_count_minute_table_sql)
    print("danmu_count_minute_table created successfully")
if not table_exists("income_minute_table"):
    cursor.execute(create_income_minute_table_sql)
    print("income_minute_table created successfully")
if not table_exists("live_status_minute_table"):
    cursor.execute(create_live_status_minute_table_sql)
    print("live_status_minute_table created successfully")

# 创建场次表
# if not table_exists("pay_count_live_table"):
#     cursor.execute(create_pay_count_live_table_sql)
#     print("pay_count_live_table created successfully")
if not table_exists("income_live_table"):
    cursor.execute(create_income_live_table_sql)
    print("income_live_table created successfully")

connection.commit()

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
    cookies['buvid3'] = BUVID3
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
    combo_send_db_index = 0
    buy_guard_db_index = 0
    user_toast_v2_db_index = 0
    super_chat_db_index = 0
    interact_word_db_index = 0

    # 写入数据库的池子的阈值
    danmu_db_threshold = 100
    gift_db_threshold = 3
    combo_send_db_threshold = 1
    buy_guard_db_threshold = 1
    user_toast_v2_db_threshold = 1
    super_chat_db_threshold = 1
    interact_word_db_threshold = 100

    # db数据对象池
    danmu_pool = []
    danmu_commit_pool = []
    gift_pool = []
    gift_commit_pool = []
    combo_send_pool = []
    combo_send_commit_pool = []
    buy_guard_pool = []
    buy_guard_commit_pool = []
    user_toast_v2_pool = []
    user_toast_v2_commit_pool = []
    super_chat_pool = []
    super_chat_commit_pool = []
    interact_word_pool = []
    interact_word_commit_pool = []

    """场次表的临时数据"""
    # 看过人数
    watch_change_dict = {}
    # 点赞人数
    like_info_update_dict = {}
    # 付费次数（暂时不用，或者后面给分钟表用）
    pay_count_dict = {}

    """分钟表的缓存数据"""
    # 高能榜已存的分钟（要区分每个主播/房间号）
    to_save_minute_online_rank_count_minute_dict = {}
    # 待存付费榜人数
    temp_online_rank_count_minute_dict = {}

    # 互动次数已存的分钟（要区分每个主播/房间号）
    to_save_minute_interact_word_count_minute_dict = {}
    # 待存互动次数
    temp_interact_word_count_minute_dict = {}

    # 进入房间人次已存的分钟（要区分每个主播/房间号）
    to_save_minute_enter_room_count_minute_dict = {}
    # 待存进入房间人次
    temp_enter_room_count_minute_dict = {}

    # 弹幕数分钟表
    to_save_minute_danmu_count_minute_dict = {}
    # 待存弹幕数
    temp_danmu_count_minute_dict = {}

    # 每分钟营收数据 已存的分钟（要区分每个主播/房间号）
    to_save_minute_income_minute_dict = {}
    # 每分钟营收数据
    temp_income_minute_dict = {}

    # # 直播状态数据 已存的分钟（要区分每个主播/房间号）
    # to_save_minute_live_status_minute_dict = {}
    # 每分钟更新直播状态
    temp_live_status_minute_dict = {}


    def _on_heartbeat(self, client: blivedm.BLiveClient, message: web_models.HeartbeatMessage):
        print(f'[{client.room_id}] 心跳')

    def _on_danmaku(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        seconds = message.timestamp / 1000
        dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{client.room_id}] [{dt}] --这是一条弹幕-- {message.uname}：{message.msg}')

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
                  'datetime': dt
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

        # 需要保存分钟表（弹幕算在互动次数里）
        # 取出当前房间号的缓存数据，分钟数和房间观众数
        if client.room_id not in self.to_save_minute_interact_word_count_minute_dict.keys():
            self.to_save_minute_interact_word_count_minute_dict[client.room_id] = 0
        if client.room_id not in self.temp_interact_word_count_minute_dict.keys():
            self.temp_interact_word_count_minute_dict[client.room_id] = 0

        cur_minute = math.floor(seconds/60)
        # 这里只负责更新数据，放在其他地方存
        if cur_minute != self.to_save_minute_interact_word_count_minute_dict[client.room_id]:
            # # 执行sql存数据库（互动次数分钟表），存的是上一分钟的数据
            if self.to_save_minute_interact_word_count_minute_dict[client.room_id] != 0:
                self.save_interact_word_count_minute_to_db(client.room_id)
            # 更新记录分钟和缓存人数
            self.temp_interact_word_count_minute_dict[client.room_id] = 0
            self.to_save_minute_interact_word_count_minute_dict[client.room_id] = cur_minute
        else:
            # 进入房间不计入互动次数
            if message.msg_type != 1:
                # 在同一分钟内不断自增
                self.temp_interact_word_count_minute_dict[client.room_id] += 1

        # 保存弹幕数分钟表
        if client.room_id not in self.to_save_minute_danmu_count_minute_dict.keys():
            self.to_save_minute_danmu_count_minute_dict[client.room_id] = 0
        if client.room_id not in self.temp_danmu_count_minute_dict.keys():
            self.temp_danmu_count_minute_dict[client.room_id] = 0

        cur_minute = math.floor(seconds/60)
        # 这里是送礼物才会触发，要写到主动下发的位置（高能榜人数）
        if cur_minute == self.to_save_minute_danmu_count_minute_dict[client.room_id]:
            # 在同一分钟内不断自增
            self.temp_danmu_count_minute_dict[client.room_id] += 1
        print(f'[{client.room_id}] [{dt}] 当前分钟已累计弹幕数：{self.temp_danmu_count_minute_dict[client.room_id]}')

    def _on_gift(self, client: blivedm.BLiveClient, message: web_models.GiftMessage):
        # gift的时间戳是秒
        seconds = message.timestamp
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

                  'timestamp': message.timestamp*1000,#改为毫秒存入数据库
                  'datetime': dt
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

        # 付费次数
        if client.room_id not in self.pay_count_dict.keys():
            self.pay_count_dict[client.room_id] = 0
        self.pay_count_dict[client.room_id] += 1
        print(f'[{client.room_id}] [{dt}] 付费次数： {self.pay_count_dict[client.room_id]}')

        # 需要保存营收分钟表
        # 取出当前房间号的缓存数据，分钟数和营收数
        current_income = round(float(message.total_coin)/1000, 1)
        self.accumulate_income_minute(client.room_id, seconds, current_income)

    def accumulate_income_minute(self, room_id, seconds, current_income):
        # 需要保存营收分钟表
        # 取出当前房间号的缓存数据，分钟数和营收数
        if room_id not in self.to_save_minute_income_minute_dict.keys():
            self.to_save_minute_income_minute_dict[room_id] = 0
        if room_id not in self.temp_income_minute_dict.keys():
            self.temp_income_minute_dict[room_id] = 0

        cur_minute = math.floor(seconds/60)
        # 这里是送礼物才会触发，要写到主动下发的位置（高能榜人数）
        if cur_minute == self.to_save_minute_income_minute_dict[room_id]:
            # 在同一分钟内不断自增
            self.temp_income_minute_dict[room_id] += current_income
        print(f'[{room_id}] 当次收入：{current_income}')

    def save_income_minute_to_db(self, room_id):
        # 需要算出待存的秒级时间戳
        to_save_second = self.to_save_minute_income_minute_dict[room_id] * 60
        to_save_datetime = datetime.fromtimestamp(to_save_second).strftime('%Y-%m-%d %H:%M:%S')
        params = {'room_id': room_id,
                  'income': self.temp_income_minute_dict[room_id],

                  'timestamp': to_save_second,
                  'datetime': to_save_datetime
                  }

        cursor.execute(insert_income_minute_table_sql, params)
        connection.commit()
        print(f'[{room_id}] [{to_save_datetime}] 存入DB，累计营收：{self.temp_income_minute_dict[room_id]}')

    def save_danmu_count_minute_to_db(self, room_id):
        # 需要算出待存的秒级时间戳
        to_save_second = self.to_save_minute_danmu_count_minute_dict[room_id] * 60
        to_save_datetime = datetime.fromtimestamp(to_save_second).strftime('%Y-%m-%d %H:%M:%S')
        params = {'room_id': room_id,
                  'count': self.temp_danmu_count_minute_dict[room_id],

                  'timestamp': to_save_second,
                  'datetime': to_save_datetime
                  }

        cursor.execute(insert_danmu_count_minute_table_sql, params)
        connection.commit()
        print(f'[{room_id}] [{to_save_datetime}] 存入DB，当前分钟弹幕数：{self.temp_danmu_count_minute_dict[room_id]}')

    def _on_combo_send(self, client: blivedm.BLiveClient, message: web_models.ComboSendMessage):
        seconds = int(round(time.time()))#单位：秒
        dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{client.room_id}] [{dt}] {message.username} 礼物连击 {message.gift_name}x{message.total_num}'
              f'，combo_num = {message.combo_num}，（瓜子x{message.combo_total_coin}）')

        params = {'room_id': client.room_id,
                  'user_id': message.uid,
                  'user_name': message.username,

                  'gift_id': message.gift_id,
                  'gift_name': message.gift_name,
                  'total_num': message.total_num,

                  'combo_id': message.combo_id,
                  'combo_num': message.combo_num,
                  'combo_total_coin': message.combo_total_coin,
                  'action': message.action,
                  'batch_combo_id': message.batch_combo_id,
                  'batch_combo_num': message.batch_combo_num,

                  'r_uid': message.r_uid,
                  'r_uname': message.r_uname,

                  'timestamp': seconds*1000,
                  'datetime': dt
                  }

        # 存入对象池
        self.combo_send_pool.append(params)
        self.combo_send_db_index += 1
        if self.combo_send_db_index >= self.combo_send_db_threshold:
            self.combo_send_commit_pool = copy.deepcopy(self.combo_send_pool)
            self.combo_send_pool = []

            # #礼物连击有报错，会导致数据库操作中断，先不存这个combosend，对其他数据没有影响
            # print("insert combo_send successfully,count = "+str(self.combo_send_db_index)+", pool count = "+str(len(self.combo_send_commit_pool)))
            self.combo_send_db_index = 0
            # cursor.executemany(insert_combo_send_table_sql, self.combo_send_commit_pool)
            # connection.commit()

    def _on_buy_guard(self, client: blivedm.BLiveClient, message: web_models.GuardBuyMessage):
        seconds = message.start_time
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

                  'timestamp': message.start_time*1000,
                  'datetime': dt
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

        # 付费次数
        if client.room_id not in self.pay_count_dict.keys():
            self.pay_count_dict[client.room_id] = 0
        self.pay_count_dict[client.room_id] += 1
        print(f'[{client.room_id}] [{dt}] 付费次数： {self.pay_count_dict[client.room_id]}')

        # 需要保存营收分钟表
        # 取出当前房间号的缓存数据，分钟数和营收数
        # 舰长使用的是金瓜子
        current_income = round(float(message.price * message.num)/1000, 1)
        self.accumulate_income_minute(client.room_id, seconds, current_income)

    def _on_user_toast_v2(self, client: blivedm.BLiveClient, message: web_models.UserToastV2Message):
        seconds = message.start_time
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

                  'timestamp': message.start_time*1000,
                  'datetime': dt
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
        seconds = message.start_time
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
                  'gift_num': message.gift_num,

                  'medal_level': message.medal_level,
                  'medal_name': message.medal_name,
                  'medal_room_id': message.medal_room_id,
                  'medal_room_uid': message.medal_ruid,

                  'start_timestamp': message.start_time*1000,
                  'end_timestamp': message.end_time*1000,
                  'datetime': dt
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

        # 付费次数
        if client.room_id not in self.pay_count_dict.keys():
            self.pay_count_dict[client.room_id] = 0
        self.pay_count_dict[client.room_id] += 1
        print(f'[{client.room_id}] [{dt}] 付费次数： {self.pay_count_dict[client.room_id]}')

        # 需要保存营收分钟表
        # 取出当前房间号的缓存数据，分钟数和营收数
        # SC使用的是人民币
        current_income = round(float(message.price * message.gift_num), 1)
        self.accumulate_income_minute(client.room_id, seconds, current_income)

    def _on_interact_word(self, client: blivedm.BLiveClient, message: web_models.InteractWordMessage):
        seconds = message.timestamp
        dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')

        temp_interact_word = {}

        if message.msg_type == 1:
            # 这个太多了，先屏蔽一下，打开试试吧
            print(f'[{client.room_id}] [{dt}] {message.username} 进入房间')
            temp_interact_word["action"] = "进入房间"
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

        # 进入房间，这个不存入互动大表
        if message.msg_type != 1:
            params = {'room_id': client.room_id,
                      'user_id': message.uid,
                      'user_name': message.username,
                      'user_face': message.face,

                      'msg_type': message.msg_type,
                      'msg_text': temp_interact_word["action"],

                      'timestamp': message.timestamp*1000,
                      'datetime': dt
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

        # 需要保存进入房间人次分钟表
        # 取出当前房间号的缓存数据，分钟数和进入房间观众数
        if client.room_id not in self.to_save_minute_enter_room_count_minute_dict.keys():
            self.to_save_minute_enter_room_count_minute_dict[client.room_id] = 0
        if client.room_id not in self.temp_enter_room_count_minute_dict.keys():
            self.temp_enter_room_count_minute_dict[client.room_id] = 0

        cur_minute = math.floor(seconds/60)
        if cur_minute != self.to_save_minute_enter_room_count_minute_dict[client.room_id]:
            # # 执行sql存数据库（互动次数分钟表），存的是上一分钟的数据
            if self.to_save_minute_enter_room_count_minute_dict[client.room_id] != 0:
                self.save_enter_room_count_minute_to_db(client.room_id)
            # 更新记录分钟和缓存人数
            self.temp_enter_room_count_minute_dict[client.room_id] = 0
            self.to_save_minute_enter_room_count_minute_dict[client.room_id] = cur_minute
        else:
            # 这里只统计进入房间消息
            if message.msg_type == 1:
                # 在同一分钟内不断自增
                self.temp_enter_room_count_minute_dict[client.room_id] += 1


        # 需要保存互动次数分钟表
        # 取出当前房间号的缓存数据，分钟数和房间观众数
        if client.room_id not in self.to_save_minute_interact_word_count_minute_dict.keys():
            self.to_save_minute_interact_word_count_minute_dict[client.room_id] = 0
        if client.room_id not in self.temp_interact_word_count_minute_dict.keys():
            self.temp_interact_word_count_minute_dict[client.room_id] = 0

        cur_minute = math.floor(seconds/60)
        if cur_minute != self.to_save_minute_interact_word_count_minute_dict[client.room_id]:
            # # 执行sql存数据库（互动次数分钟表），存的是上一分钟的数据
            if self.to_save_minute_interact_word_count_minute_dict[client.room_id] != 0:
                self.save_interact_word_count_minute_to_db(client.room_id)
            # 更新记录分钟和缓存人数
            self.temp_interact_word_count_minute_dict[client.room_id] = 0
            self.to_save_minute_interact_word_count_minute_dict[client.room_id] = cur_minute
        else:
            # 进入房间不计入互动次数
            if message.msg_type != 1:
                # 在同一分钟内不断自增
                self.temp_interact_word_count_minute_dict[client.room_id] += 1

    def save_enter_room_count_minute_to_db(self, room_id):
        # 需要算出待存的秒级时间戳
        to_save_second = self.to_save_minute_enter_room_count_minute_dict[room_id] * 60
        to_save_datetime = datetime.fromtimestamp(to_save_second).strftime('%Y-%m-%d %H:%M:%S')
        params = {'room_id': room_id,
                  'count': self.temp_enter_room_count_minute_dict[room_id],

                  'timestamp': to_save_second,
                  'datetime': to_save_datetime
                  }

        cursor.execute(insert_enter_room_count_minute_table_sql, params)
        connection.commit()
        print(f'[{room_id}] [{to_save_datetime}] 存入DB，进入房间人次：{self.temp_enter_room_count_minute_dict[room_id]}')


    def save_interact_word_count_minute_to_db(self, room_id):
        # 需要算出待存的秒级时间戳
        to_save_second = self.to_save_minute_interact_word_count_minute_dict[room_id] * 60
        to_save_datetime = datetime.fromtimestamp(to_save_second).strftime('%Y-%m-%d %H:%M:%S')
        params = {'room_id': room_id,
                  'count': self.temp_interact_word_count_minute_dict[room_id],

                  'timestamp': to_save_second,
                  'datetime': to_save_datetime
                  }

        cursor.execute(insert_interact_word_count_minute_table_sql, params)
        connection.commit()
        print(f'[{room_id}] [{to_save_datetime}] 存入DB，互动次数：{self.temp_interact_word_count_minute_dict[room_id]}')



    def _on_watch_change(self, client: blivedm.BLiveClient, message: web_models.WatchChangeMessage):
        cur_timestamp = int(round(time.time()))#单位：秒
        cur_dt = datetime.fromtimestamp(cur_timestamp).strftime('%Y-%m-%d %H:%M:%S')

        watch_count = message.num

        # 最新的watch_count覆盖到临时字典里
        if client.room_id not in self.watch_change_dict:
            self.watch_change_dict[client.room_id] = 0
        self.watch_change_dict[client.room_id] = watch_count

        print(f'[{client.room_id}] [{cur_dt}] {watch_count}人看过')

    def _on_like_info_update(self, client: blivedm.BLiveClient, message: web_models.LikeInfoUpdateMessage):
        cur_timestamp = int(round(time.time()))#单位：秒
        cur_dt = datetime.fromtimestamp(cur_timestamp).strftime('%Y-%m-%d %H:%M:%S')

        like_count = message.click_count

        if client.room_id not in self.like_info_update_dict:
            self.like_info_update_dict[client.room_id] = 0
        self.like_info_update_dict[client.room_id] = like_count

        print(f'[{client.room_id}] [{cur_dt}] {like_count}点赞')

    def _on_start_live(self, client: blivedm.BLiveClient, message: web_models.StartLiveMessage):
        cur_timestamp = time.time()#单位：秒
        cur_dt = datetime.fromtimestamp(cur_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{client.room_id}] [{cur_dt}] {message.room_id}开始直播，live_id = {message.live_key}')

    def _on_online_rank_count(self, client: blivedm.BLiveClient, message: web_models.OnlineRankCountMessage):
        cur_timestamp = int(round(time.time()))#单位：秒
        cur_dt = datetime.fromtimestamp(cur_timestamp).strftime('%Y-%m-%d %H:%M:%S')

        # 取出当前房间号的缓存数据，分钟数和房间观众数
        if client.room_id not in self.to_save_minute_online_rank_count_minute_dict.keys():
            self.to_save_minute_online_rank_count_minute_dict[client.room_id] = 0
        if client.room_id not in self.temp_online_rank_count_minute_dict.keys():
            self.temp_online_rank_count_minute_dict[client.room_id] = 0

        cur_minute = math.floor(cur_timestamp/60)
        if cur_minute != self.to_save_minute_online_rank_count_minute_dict[client.room_id]:
            # 这里是一定会下发的，所以把【【【营收】】】也放在这里存。执行sql存数据库（付费榜人数分钟表），存的是上一分钟的数据
            if self.to_save_minute_online_rank_count_minute_dict[client.room_id] != 0:
                self.save_online_rank_count_minute_to_db(client.room_id)
                self.save_income_minute_to_db(client.room_id)
                self.save_danmu_count_minute_to_db(client.room_id)

                # 每分钟获取直播状态
                self.get_live_status(client.room_id,cur_minute*60)

                # # 测试：看过和点赞先放在这每分钟存（和整分钟错开）
                # self.save_watch_change_to_db(client.room_id, cur_timestamp, cur_dt)
                # self.save_like_info_update_to_db(client.room_id, cur_timestamp, cur_dt)

                # # 测试：当前直播场次到当前时刻的营收数据
                # # 需要将场次表各个信息的数据存入DB
                # room_id = client.room_id
                # dt = cur_dt
                # watch_change_count = 0
                # if room_id in self.watch_change_dict.keys():
                #     watch_change_count = self.watch_change_dict[room_id]
                # like_info_update_count = 0
                # if room_id in self.like_info_update_dict.keys():
                #     like_info_update_count = self.like_info_update_dict[room_id]
                # 
                # # 先要找最近一次的开始直播的时间
                # pay_count = 0
                # total_income = 0
                # pay_result = {}
                # execution_time = 0
                # cur_day = datetime.fromtimestamp(cur_timestamp).strftime('%Y-%m-%d')
                # start_time_str, end_time_str, execution_time = query_live_start_end_time_by_live_date(db_config,room_id,cur_day)
                # cur_day_date = datetime.strptime(cur_day, '%Y-%m-%d')
                # start_time_date = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                # if cur_day_date.date() == start_time_date.date():
                #     pay_count, total_income, pay_result, execution_time = query_pay_count_by_room_and_live_start_end_time(db_config, room_id, start_time_str, dt)
                # 
                # self.save_income_live_to_db(room_id, start_time_str, dt, pay_count, total_income,
                #                             watch_change_count, like_info_update_count, cur_timestamp, dt)

            # 更新记录分钟和缓存人数
            self.temp_online_rank_count_minute_dict[client.room_id] = message.count
            self.to_save_minute_online_rank_count_minute_dict[client.room_id] = cur_minute
            # 更新营收记录分钟和缓存营收
            self.temp_income_minute_dict[client.room_id] = 0
            self.to_save_minute_income_minute_dict[client.room_id] = cur_minute
            # 更新弹幕数记录分钟和缓存分钟弹幕数
            self.temp_danmu_count_minute_dict[client.room_id] = 0
            self.to_save_minute_danmu_count_minute_dict[client.room_id] = cur_minute
        else:
            # 不断覆盖
            self.temp_online_rank_count_minute_dict[client.room_id] = message.count

        count = message.count
        print(f'[{client.room_id}] [{cur_dt}] 高能榜人数：{count}')

    def save_online_rank_count_minute_to_db(self, room_id):
        # 需要算出待存的秒级时间戳
        to_save_second = self.to_save_minute_online_rank_count_minute_dict[room_id] * 60
        to_save_datetime = datetime.fromtimestamp(to_save_second).strftime('%Y-%m-%d %H:%M:%S')
        params = {'room_id': room_id,
                  'count': self.temp_online_rank_count_minute_dict[room_id],

                  'timestamp': to_save_second,
                  'datetime': to_save_datetime
                  }

        cursor.execute(insert_online_rank_count_minute_table_sql, params)
        connection.commit()
        print(f'[{room_id}] [{to_save_datetime}] 存入DB，高能榜人数：{self.temp_online_rank_count_minute_dict[room_id]}')

    def get_live_status(self, room_id, in_seconds=0):
        cur_timestamp = in_seconds
        # 如果没传入整分钟的时间戳，那就拿当前时间戳
        if cur_timestamp == 0:
            cur_timestamp = int(round(time.time()))#单位：秒
        dt = datetime.fromtimestamp(cur_timestamp).strftime('%Y-%m-%d %H:%M:%S')

        if room_id not in self.temp_live_status_minute_dict.keys():
            self.temp_live_status_minute_dict[room_id] = -1

        try:
            # 创建带重试机制的Session
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=1, status_forcelist=[500,502,503,504])
            session.mount('https://', HTTPAdapter(max_retries=retries))

            # 发送带浏览器头的请求
            response = session.get(
                "https://api.live.bilibili.com/room/v1/Room/get_info",
                params={'room_id': room_id},
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'Referer': f'https://live.bilibili.com/{room_id}'
                },
                timeout=5
            )
            response.raise_for_status()

            result = response.json()
            if result.get('code') == 0:
                data = result['data']
                if data['live_status'] == 1:
                    start_time_str = data['live_time']
                    dt_obj = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                    print(f"[{room_id}] [{dt}] 直播状态：直播中, live_start_time = {start_time_str},"
                          f" timestamp = {int(dt_obj.timestamp())}, title = {data['title']}")
                elif data['live_status'] == 2:
                    print(f"[{room_id}] [{dt}] 直播状态：轮播中, title = {data['title']}")
                elif data['live_status'] == 0:
                    print(f"[{room_id}] [{dt}] 直播状态：未开播")
            else:
                print(f"API错误: {result.get('message')} (code:{result.get('code')})")

        except requests.exceptions.RequestException as e:
            print(f"网络请求异常: {str(e)}")
        except KeyError as e:
            print(f"响应数据格式异常，缺失字段: {str(e)}")

        # 从0、2变为1是开始直播，从1变为0、2是结束直播
        live_action = '无'
        if self.temp_live_status_minute_dict[room_id] == 0 or self.temp_live_status_minute_dict[room_id] == 2:
            if data['live_status'] == 1:
                live_action = '开始直播'
        elif self.temp_live_status_minute_dict[room_id] == 1:
            if data['live_status'] == 0 or data['live_status'] == 2:
                live_action = '结束直播'

        self.temp_live_status_minute_dict[room_id] = data['live_status']

        params = {'room_id': room_id,
                  'live_status': data['live_status'],
                  'live_action': live_action,

                  'timestamp': cur_timestamp,
                  'datetime': dt
                  }

        cursor.execute(insert_live_status_minute_table_sql, params)
        connection.commit()
        print(f"[{room_id}] [{dt}] 存入DB，直播状态：{data['live_status']}，直播动作：{live_action}")

        # 需要上面分钟的直播状态存入db后，才能取出来最新的数据
        # 从0、2变为1是开始直播，从1变为0、2是结束直播
        if self.temp_live_status_minute_dict[room_id] == 0 or self.temp_live_status_minute_dict[room_id] == 2:
            if data['live_status'] == 1:
                live_action = '开始直播'
        elif self.temp_live_status_minute_dict[room_id] == 1:
            if data['live_status'] == 0 or data['live_status'] == 2:
                live_action = '结束直播'
                # 下播时将看过和点赞存入数据库
                self.save_watch_change_to_db(room_id, cur_timestamp, dt)
                self.save_like_info_update_to_db(room_id, cur_timestamp, dt)

                # 需要将场次表各个信息的数据存入场次表DB
                watch_change_count = 0
                if room_id in self.watch_change_dict.keys():
                    watch_change_count = self.watch_change_dict[room_id]
                like_info_update_count = 0
                if room_id in self.like_info_update_dict.keys():
                    like_info_update_count = self.like_info_update_dict[room_id]

                # 先要找最近一次的开始直播的时间
                pay_count = 0
                total_income = 0
                cur_day = datetime.fromtimestamp(cur_timestamp).strftime('%Y-%m-%d')
                cur_day_zero_time = datetime.fromtimestamp(cur_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                pair_list, execution_time = \
                    query_live_start_end_time_by_live_date(db_config, room_id, cur_day, date_is_start_live_date=False)

                # 在pairlist里面找最新的pair再取出 start_time
                if len(pair_list) > 0:
                    latest_pair = pair_list[-1]
                    if 'start_time_str' in latest_pair.keys():
                        start_live_time_str = latest_pair['start_time_str']
                    else:
                        # 取出当天的0点时间
                        start_live_time_str = cur_day_zero_time
                else:
                    # 取出当天的0点时间
                    start_live_time_str = cur_day_zero_time

                cur_day_date = datetime.strptime(cur_day, '%Y-%m-%d')
                start_time_time = datetime.strptime(start_live_time_str, '%Y-%m-%d %H:%M:%S')
                if cur_day_date.date() == start_time_time.date():
                    pay_count, total_income, pay_result, execution_time = \
                        query_pay_count_by_room_and_live_start_end_time(db_config, room_id, start_live_time_str, dt)

                # 开始存
                self.save_income_live_to_db(room_id, start_live_time_str, dt, pay_count, total_income,
                                            watch_change_count, like_info_update_count, cur_timestamp, dt)

    def save_watch_change_to_db(self, room_id, seconds, dt):
        if room_id not in self.watch_change_dict.keys():
            return

        params = {'room_id': room_id,
                  'count': self.watch_change_dict[room_id],

                  'timestamp': seconds,
                  'datetime': dt
                  }

        cursor.execute(insert_watch_change_table_sql, params)
        connection.commit()
        print(f"[{room_id}] [{dt}] 存入DB，当前场次 观看人次：{self.watch_change_dict[room_id]}")

    def save_like_info_update_to_db(self, room_id, seconds, dt):
        if room_id not in self.like_info_update_dict.keys():
            return

        params = {'room_id': room_id,
                  'count': self.like_info_update_dict[room_id],

                  'timestamp': seconds,
                  'datetime': dt
                  }

        cursor.execute(insert_like_info_update_table_sql, params)
        connection.commit()
        print(f"[{room_id}] [{dt}] 存入DB，当前场次 点赞次数：{self.like_info_update_dict[room_id]}")

    # def save_pay_count_live_to_db(self, room_id, pay_count, seconds, dt):
    #     params = {'room_id': room_id,
    #               'pay_count': pay_count,
    # 
    #               'timestamp': seconds,
    #               'datetime': dt
    #               }
    # 
    #     cursor.execute(insert_pay_count_live_table_sql, params)
    #     connection.commit()
    #     print(f"[{room_id}] [{dt}] 存入DB，当前场次 付费次数：{pay_count}")

    def save_income_live_to_db(self, room_id, start_time_str, end_time_str, pay_count,  income,
                               watch_change_count, like_info_update_count, seconds, dt):
        params = {'room_id': room_id,
                  'start_time_str': start_time_str,
                  'end_time_str': end_time_str,

                  'pay_count': pay_count,
                  'income': income,
                  'watch_change_count': watch_change_count,
                  'like_info_update_count': like_info_update_count,

                  'timestamp': seconds,
                  'datetime': dt
                  }

        cursor.execute(insert_income_live_table_sql, params)
        connection.commit()
        print(f"[{room_id}] [{dt}] 存入DB，当前场次 开始时间：{start_time_str}，结束时间：{end_time_str}，"
              f"付费次数：{pay_count}，总营收：{income}，观看人次：{watch_change_count}，点赞次数：{like_info_update_count}")


if __name__ == '__main__':
    asyncio.run(main())
