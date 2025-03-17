import datetime
from zoneinfo import ZoneInfo
import discord
from discord.ext import commands
import os
import openai
from openai import OpenAI
import json
from threading import Thread
import time
import pytz
import base64

class DrawOpenai:
    def __init__(self, config):
        self.config = config
        # openai_conf_obj = open("./config/openai_conf.json","r")
        # openai_config = json.load(openai_conf_obj)
        #openai.api_key = config["OPENAI_API_KEY"]
        os.environ["OPENAI_API_KEY"] = config["OPENAI_API_KEY"]
        self.client = OpenAI()
        #self.client.api_key = config["OPENAI_API_KEY"]
        self.message_dic = {}
        self.tmp_dir_path = self.config["tmp_dir_path"]

    def delete_chat_log(self):
        for thread_id in list(self.message_dic.keys()):
            create_time = datetime.datetime.strptime(
                self.message_dic[thread_id]["start_time"], "%Y-%m-%d %H:%M"
            ).replace(tzinfo=pytz.timezone("Asia/Tokyo"))
            now_time = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
            delta = now_time - create_time
            if delta.days >= 1:
                del self.message_dic[thread_id]

    def check_chatgpt_thread(self, thread_id):
        """
        すでにchatのスレッドが立っているか確認するための
        """
        if thread_id in self.message_dic:
            return True
        else:
            return False


    async def call_openai(self, prompt):
        """
        chat gptに問い合わせるための関数
        """
        # APIリクエストの設定
        response = self.client.images.generate(
            model=self.config["model"],
            prompt=prompt,
            size=self.config["size"],
            quality=self.config["quality"],
            response_format="b64_json",
            n=1,
        )
        return response

    async def response_chatgpt(self, thread, prompt):
        """
        discordにchat-gptのレスポンスを返すための関数
        """
        response = await self.call_openai(prompt)
        image_bytes = base64.b64decode(response.data[0].b64_json)
        os.makedirs(self.tmp_dir_path, exist_ok=True)
        img_path = os.path.join(self.tmp_dir_path, "tmp.png")
        with open(img_path,"wb") as fb:
            fb.write(image_bytes)
        await thread.send(file=discord.File(img_path))

    async def new_draw_chat(self, ctx):
        """
        /draw-dalleコマンドが呼ばれた時の処理。新たにスレッドを立てる
        """
        channel = ctx.channel  # メッセージがあったチャンネルの取得
        # スレッド名の定義
        date = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
        date_str = date.strftime("%Y-%m-%d %H:%M")
        thread_name = "{}".format(date_str)
        # スレッドの作成
        thread = await channel.create_thread(
            name=thread_name,
            reason="make chat",
            type=discord.ChannelType.public_thread,
            auto_archive_duration=60,
        )  # スレッドを作る
        date = datetime.datetime.now()
        self.message_dic[thread.id] = {}
        self.message_dic[thread.id]["start_time"] = date.strftime("%Y-%m-%d %H:%M")
        # メッセージを送信してスレッドを開始します。
        await thread.send(
            "chat-gptにお絵描きをしてもらう用のスレッドです。どんな絵が良いか日本語で入力してください")
