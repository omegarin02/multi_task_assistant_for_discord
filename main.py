import discord
from discord.ext import commands, tasks
import json
import shutil
import datetime
from task_scr import (
    help,
    parrot,
    chat_openai,
    auto_post_arrange_schedule,
    draw_openai
)

# configの読み込み
config_file = open("./config/config.json", "r", encoding="utf-8")
config = json.load(config_file)
common_config = config["common"]
function_config = config["function"]

parrot_config = function_config["parrot"]
chat_openai_config = function_config["chat_openai"]
draw_openai_config = function_config["draw_openai"]
#live_scheduler_config = function_config["live_scheduler"]
auto_post_arrange_schedule_config = function_config["auto_post_arrange_schedule"]

## 各機能ごとのconfig取り出し
help_cls = help.ShowHelp()
parrot_cls = parrot.Parrot(parrot_config) if parrot_config["use"] == True else None
chat_openai_cls = (
    chat_openai.ChatOpenai(chat_openai_config)
    if chat_openai_config["use"] == True
    else None
)

draw_openai_cls = (
    draw_openai.DrawOpenai(draw_openai_config)
    if draw_openai_config["use"] == True
    else None
)

auto_post_arrange_schedule_cls = (
    auto_post_arrange_schedule.AutoPostArrangeSchedule(
        auto_post_arrange_schedule_config["settings"]
    )
    if auto_post_arrange_schedule_config["use"] == True
    else None
)

##必用な設定値を読み出し
discord_api_key = common_config["discord_api_key"]


# replitを使用する場合に必要なライブラリを読み込み
if common_config["use_replit"]:
    from server import keep_alive  # ToDo ない場合は読み込まない

# discordbotの設定
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True  # メッセージに関するデバッグ情報を有効化
client = commands.Bot(command_prefix="/", intents=intents)


# bot用スクリプト
# 自動投稿用スクリプト
@tasks.loop(minutes=1)
async def wrapper_auto_post_arrange_schedule():
    if(auto_post_arrange_schedule_cls is not None):
        for config in auto_post_arrange_schedule_cls.settings:
            ctx = client.get_channel(config["channel_id"])
            await auto_post_arrange_schedule_cls.scheduled_message(ctx,config)
    else:
        pass


@client.event
async def on_ready():
    print("ログインしました")
    wrapper_auto_post_arrange_schedule.start()

# メッセージを受信したときの処理
@client.event
async def on_message(message):  # メッセージをなにかしら受け取ったときの処理
    if type(message.channel) is discord.Thread:  # スレッドでメッセージを受け取った時
        if message.author == client.user or message.author.bot:  # メッセージの送り主がbotの時は処理しない
            pass
        elif (
            False
        ):  # message.channel.id not in allow_recoed_thread_id:  #録画を許可しないスレッドは処理しない
            pass
        else:  # ここに保存コマンドを書く
            # chatgptへの問い合わせ場合
            if (
                chat_openai_cls != None
                and chat_openai_config["commands"]["chat"]["use"] == True
            ):
                if chat_openai_cls.check_chatgpt_thread(message.channel.id):
                    await chat_openai_cls.response_chatgpt(
                        message.channel, message.content
                    )
                # 暫定処置：時間切れになったスレッドのログを削除する
                chat_openai_cls.delete_chat_log()
            # chatgptへの問い合わせ場合
            if (
                draw_openai_cls != None
                and draw_openai_config["commands"]["draw-dalle"]["use"] == True
            ):
                if draw_openai_cls.check_chatgpt_thread(message.channel.id):
                    await draw_openai_cls.response_chatgpt(
                        message.channel, message.content
                    )
                # 暫定処置：時間切れになったスレッドのログを削除する
                draw_openai_cls.delete_chat_log()
            if (
                live_scheduler_cls != None
                and live_scheduler_config["commands"]["schedule-edit"]["use"] == True
            ):
                if live_scheduler_cls.check_schedule_editing(message.channel.id):
                    await live_scheduler_cls.edit_schedule(
                        message.channel, message.content
                    )

    # それ以外はコマンド実行
    if message.author == client.user or message.author.bot:
        pass
    else:
        pass
        # await message.channel.send('メッセージを受信しました。')
    await client.process_commands(message)


@client.command("bot-help")
async def wrapper_help(ctx):
    await help_cls.show_help(ctx, function_config)


# オウム返し
@client.command("parrot")
async def wrapper_parrot(ctx, text):
    if parrot_cls != None:
        await parrot_cls.parrot(ctx, text)
    else:
        await ctx.send("この機能は使用できません。")


# chat GPTによるチャット
@client.command("chat")
async def wrapper_chat_openai(ctx):
    try:
        if chat_openai_cls != None:
            chat_openai_cls.delete_chat_log()
            await chat_openai_cls.new_chat(ctx)
        else:
            await ctx.send("この機能は使用できません。")
    except Exception as e:
        await ctx.send("Errorが発生しました。次のメッセージをbot管理者にお伝えください。\n {}".format(str(e)))


# chat GPTによるチャット
@client.command("draw-dalle")
async def wrapper_new_draw_chat(ctx):
    try:
        if draw_openai_cls != None:
            draw_openai_cls.delete_chat_log()
            await draw_openai_cls.new_draw_chat(ctx)
        else:
            await ctx.send("この機能は使用できません。")
    except Exception as e:
        await ctx.send("Errorが発生しました。次のメッセージをbot管理者にお伝えください。\n {}".format(str(e)))


# ウェブサーバーを起動する
# ToDo ない場合は読み込まない
if common_config["use_replit"]:
    keep_alive()

client.run(discord_api_key)
