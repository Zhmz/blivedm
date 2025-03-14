# -*- coding: utf-8 -*-
import asyncio
import http.cookies
import random
from datetime import datetime
from typing import *

import aiohttp

import blivedm
import blivedm.models.web as web_models
import json
from pathlib import Path

# 直播间ID的取值看直播间URL
TEST_ROOM_IDS = [
    22389206,#折原露露
    27183290,#雪糕cheese
    31835822,#萝尔露Real
    7688602,#花花Haya
    22816111,#东雪莲
    21652717,#白神遥
    22992234,#蕾尔娜Leona
]

# 需要存入文件的字典
danmu_dict = {}


# 这里填一个已登录账号的cookie的SESSDATA字段的值。不填也可以连接，但是收到弹幕的用户名会打码，UID会变成0
SESSDATA = '2726d111%2C1757406746%2Ca9e96%2A31CjDCbdBS3F4ouVfQVtpDA-gMErg6XzwDUzfmIZF3BxsrWc64whXOpmNTc363zO3BKzMSVno1OHlTZkFaejRaU2tfWEZpbVNVZkx6dGVyem1OemxTVXFWUUtGdUNIZ0FxNWJ3cDRyTVlhLUFIOTFMN1FQSmVoUDZxRnJKWU9HdUlOOEp6cllrdXpnIIEC'

session: Optional[aiohttp.ClientSession] = None


async def main():
    init_danmu_dict()
    init_session()
    try:
        await run_single_client()
        await run_multi_clients()
    finally:
        await session.close()


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


# 初始化字典
def init_danmu_dict():
    for room_id in TEST_ROOM_IDS:
        if room_id not in danmu_dict:
            danmu_dict[room_id] = {}


class MyHandler(blivedm.BaseHandler):
    # # 演示如何添加自定义回调
    # _CMD_CALLBACK_DICT = blivedm.BaseHandler._CMD_CALLBACK_DICT.copy()
    #
    # # 看过数消息回调
    # def __watched_change_callback(self, client: blivedm.BLiveClient, command: dict):
    #     print(f'[{client.room_id}] WATCHED_CHANGE: {command}')
    # _CMD_CALLBACK_DICT['WATCHED_CHANGE'] = __watched_change_callback  # noqa


    # 计数器，达到阈值后写入一次文件
    danmu_instance_index = 0
    # 写入文件的阈值
    danmu_threshold = 100

    json_file_name = 'danmu.json'


    def save_danmu_to_json(self):
        try:
            with Path(self.json_file_name).open("w", encoding="utf-8") as f:
                json.dump(danmu_dict, f, ensure_ascii=False, indent=4)
            print(f"数据已保存至 {self.json_file_name}")
        except (IOError, TypeError) as e:
            print(f"保存失败：{str(e)}")

    def _on_heartbeat(self, client: blivedm.BLiveClient, message: web_models.HeartbeatMessage):
        print(f'[{client.room_id}] 心跳')

    def _on_danmaku(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        seconds = message.timestamp/1000
        dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{client.room_id}] [{dt}] {message.uname}：{message.msg}')

        if client.room_id in danmu_dict.keys():
            if "danmu" not in danmu_dict[client.room_id]:
                danmu_dict[client.room_id]["danmu"] = list()
            temp_danmu = {}
            temp_danmu["datetime"] = dt
            temp_danmu["username"] = message.uname
            temp_danmu["msg"] = message.msg
            danmu_dict[client.room_id]["danmu"].append(temp_danmu)
            self.danmu_instance_index += 1

            if self.danmu_instance_index >= self.danmu_threshold:
                self.danmu_instance_index = 0
                self.save_danmu_to_json()

    def _on_gift(self, client: blivedm.BLiveClient, message: web_models.GiftMessage):
        seconds = message.timestamp/1000
        dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{client.room_id}] [{dt}] {message.uname} 赠送{message.gift_name}x{message.num}'
              f' （{message.coin_type}瓜子x{message.total_coin}）')

    def _on_buy_guard(self, client: blivedm.BLiveClient, message: web_models.GuardBuyMessage):
        seconds = message.timestamp/1000
        dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{client.room_id}] [{dt}] {message.username} 上舰，guard_level={message.guard_level}')

    def _on_user_toast_v2(self, client: blivedm.BLiveClient, message: web_models.UserToastV2Message):
        seconds = message.start_time/1000
        dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{client.room_id}] [{dt}] {message.username} 上舰，guard_level={message.guard_level}')

    def _on_super_chat(self, client: blivedm.BLiveClient, message: web_models.SuperChatMessage):
        seconds = message.timestamp/1000
        dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{client.room_id}] [{dt}] 醒目留言 ¥{message.price} {message.uname}：{message.message}')

    # def _on_interact_word(self, client: blivedm.BLiveClient, message: web_models.InteractWordMessage):
    #     seconds = message.timestamp/1000
    #     dt = datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')
    #     if message.msg_type == 1:
    #         print(f'[{client.room_id}] [{dt}] {message.username} 进入房间')
    #     elif message.msg_type == 2:
    #         print(f'[{client.room_id}] [{dt}] {message.username} 关注了主播')
    #     elif message.msg_type == 3:
    #         print(f'[{client.room_id}] [{dt}] {message.username} 分享了房间')
    #     elif message.msg_type == 4:
    #         print(f'[{client.room_id}] [{dt}] {message.username} 特别关注了主播')
    #     elif message.msg_type == 5:
    #         print(f'[{client.room_id}] [{dt}] {message.username} 与主播互粉了')
    #     elif message.msg_type == 6:
    #         print(f'[{client.room_id}] [{dt}] {message.username} 为主播点赞了')


if __name__ == '__main__':
    asyncio.run(main())
