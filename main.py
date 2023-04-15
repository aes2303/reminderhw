import asyncio, discord, mysql.connector, os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv, find_dotenv
from discord.ext import tasks

from database import Database

load_dotenv(find_dotenv(), verbose=True)
client = discord.Client()

DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
GUILD_IDS = [int(os.environ.get('GUILD_ID'))]
NOTIFY_CHANNEL_NAME = os.environ.get('NOTIFY_CHANNEL_NAME')

intents = discord.Intents.all()
bot = discord.Bot(command_prefix="/", intents=intents)
database = Database(
    os.environ.get('HOST'),
    os.environ.get('USER'),
    os.environ.get('PASSWORD'),
    os.environ.get('DATABASE')
)

async def send_message(ctx, title, description, color, ephemeral):
    embed = discord.Embed(title=title, description=description, color=color)
    await ctx.respond(embed=embed, ephemeral=ephemeral)

async def notify_message(bot, title, description, color):
    channel = discord.utils.get(bot.get_all_channels(), name=NOTIFY_CHANNEL_NAME)
    embed = discord.Embed(title=title, description=description, color=color)
    notify_role_id = discord.utils.get(channel.guild.roles, name="notify").id
    await channel.send(f"<@&{notify_role_id}>", embed=embed)

@bot.event
async def on_ready():
    periodic_func.start()
    for guild in bot.guilds:
        if not discord.utils.get(guild.roles, name="notify"):
            await guild.create_role(name="notify")

@bot.slash_command(guild_ids=GUILD_IDS)
async def notify_me(ctx, notify: bool):
    """メンションによる通知を受け取るかどうかを設定する"""
    role = discord.utils.get(ctx.guild.roles, name="notify")
    if notify:
        await ctx.author.add_roles(role)
        await send_message(ctx, "Reminder HW", "通知を受け取るように設定したよ！", 0x00ff00, True)
    else:
        await ctx.author.remove_roles(role)
        await send_message(ctx, "Reminder HW", "通知を受け取らないように設定したよ！", 0x00ff00, True)

@bot.slash_command(guild_ids=GUILD_IDS)
async def add_hw(ctx, subject: str, hw: str, due_date: str):
    """課題を追加する"""
    subjects = database.get_subjects()
    if subject not in [subject[0] for subject in subjects]:
        if len(subjects) == 0:
            await send_message(ctx, "Reminder HW", "教科が登録されてないよ！", 0xff0000, True)
            return
        subjects = "\n".join([f"- {subject[0]}" for subject in subjects])
        await send_message(ctx, "Reminder HW", f"その教科は登録されてないよ！\n登録されている教科一覧\n{subjects}", 0xff0000, True)
        return

    try:
        datetime.strptime(due_date, '%Y/%m/%d')
    except ValueError:
        await send_message(ctx, "Reminder HW", "期限の形式が違うよ！\nYYYY/MM/DDで入力してね！", 0xff0000, True)
        return

    if (datetime.strptime(due_date, '%Y/%m/%d') - datetime.now()).days < 0:
        await send_message(ctx, "Reminder HW", "期限が過去の日付だよ！", 0xff0000, True)
        return

    if database.add_hw(subject, hw, due_date):
        await send_message(ctx, "Reminder HW", f"以下の内容で追加したよ！\n教科: {subject}\n課題: {hw}\n期限: {due_date}", 0x00ffff, False)
    else:
        await send_message(ctx, "Reminder HW", "その課題は既に登録されてるよ！", 0xff0000, True)

@bot.slash_command(guild_ids=GUILD_IDS)
async def get_hw_week(ctx):
    """1週間以内の全ての課題を取得する"""
    homework = database.get_all_hw()
    homework = [hw for hw in homework if 0 <= (datetime.strptime(hw[2], "%Y/%m/%d") - datetime.now()).days + 1 <= 6]
    if homework:
        homework = "\n".join([f"[{hw[0]}] {hw[1]} ({hw[2]})" for hw in homework])
        await send_message(ctx, "Reminder HW", homework, 0x00ffff, True)
    else:
        await send_message(ctx, "Reminder HW", "課題は登録されてないよ！", 0xff0000, True)

@bot.slash_command(guild_ids=GUILD_IDS)
async def get_hw_month(ctx):
    """30日以内の教科の課題を取得する"""
    homework = database.get_all_hw()
    homework = [hw for hw in homework if 0 <= (datetime.strptime(hw[2], "%Y/%m/%d") - datetime.now()).days + 1 <= 29]
    if homework:
        homework = "\n".join([f"[{hw[0]}] {hw[1]} ({hw[2]})" for hw in homework])
        await send_message(ctx, "Reminder HW", homework, 0x00ffff, True)
    else:
        await send_message(ctx, "Reminder HW", "課題は登録されてないよ！", 0xff0000, True)

@bot.slash_command(guild_ids=GUILD_IDS)
async def delete_hw(ctx, subject: str, hw: str, due_date: str):
    """課題を削除する"""
    if database.delete_hw(subject, hw, due_date):
        await send_message(ctx, "Reminder HW", f"教科: {subject}\n課題: {hw}\n期限: {due_date}\nを削除したよ！", 0x00ffff, False)
    else:
        await send_message(ctx, "Reminder HW", "その課題は登録されてないよ！", 0xff0000, True)

@bot.slash_command(guild_ids=GUILD_IDS)
async def add_subject(ctx, subject: str):
    """教科を追加する"""
    if database.add_subject(subject):
        await send_message(ctx, "Reminder HW", f"教科: {subject}\nを追加したよ!", 0x00ffff, False)
    else:
        await send_message(ctx, "Reminder HW", "その教科は既に登録されてるよ！", 0xff0000, True)

@bot.slash_command(guild_ids=GUILD_IDS)
async def get_subjects(ctx):
    """教科を取得する"""
    subjects = database.get_subjects()
    if subjects:
        subjects = "\n".join([f"教科: {subject[0]}" for subject in subjects])
        await send_message(ctx, "Reminder HW", subjects, 0x00ffff, True)
    else:
        await send_message(ctx, "Reminder HW", "教科は登録されてないよ！", 0xff0000, True)

@bot.slash_command(guild_ids=GUILD_IDS)
async def delete_subject(ctx, subject: str):
    """教科を削除する"""
    if database.delete_subject(subject):
        await send_message(ctx, "Reminder HW", f"教科: {subject}\nを削除したよ!", 0x00ffff, False)
    else:
        await send_message(ctx, "Reminder HW", "その教科は登録されてないよ！", 0xff0000, True)

@bot.slash_command(guild_ids=GUILD_IDS)
async def help(ctx):
    command_and_description = {
        "/notify_me": "通知を受け取るかどうかを設定する",
        "/add_hw": "課題を追加する",
        "/get_hw_week": "1週間以内の課題を取得する",
        "/get_hw_month": "30日以内の全ての課題を取得する",
        "/delete_hw": "課題を削除する",
        "/add_subject": "教科を追加する",
        "/get_subjects": "教科を取得する",
        "/delete_subject": "教科を削除する",
    }
    await send_message(ctx, "Reminder HW", "\n".join([f"{command}: {description}" for command, description in command_and_description.items()]), 0x00ff00, True)

# 1週間以内の課題を取得して、期限が近い順に並べて通知する
async def task():
    homework = database.get_all_hw()
    homework = [hw for hw in homework if 0 <= (datetime.strptime(hw[2], "%Y/%m/%d") - datetime.now()).days + 1 <= 6]
    if homework:
        homework = sorted(homework, key=lambda x: datetime.strptime(x[2], "%Y/%m/%d"))
        homework = "\n".join([f"[{hw[0]}] {hw[1]} ({hw[2]})" for hw in homework])
        await notify_message(bot, "Half Day Reminder", f"1週間以内の課題を通知します\n今日の日付: {datetime.now().strftime('%Y/%m/%d')}\n{homework}", 0xffff00)
    else:
        await notify_message(bot, "Half Day Reminder", "1週間以内の課題は登録されてないよ！", 0xffff00)

@tasks.loop(seconds=40)
async def periodic_func():
    now = datetime.now(timezone(timedelta(hours=9))).strftime('%H:%M')
    if now == '00:00' or now == '12:00':
        await task()


if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
