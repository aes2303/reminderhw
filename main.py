import discord, os
from discord.ext import pages, tasks
from dotenv import find_dotenv, load_dotenv

from database import Database
from util import *

load_dotenv(find_dotenv(), verbose=True)
client = discord.Client()

DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
GUILD_IDS = [int(os.environ.get('GUILD_ID'))]
NOTIFY_CHANNEL_NAME = os.environ.get('NOTIFY_CHANNEL_NAME')
NOTIFY_ROLE_NAME = os.environ.get('NOTIFY_ROLE_NAME')
NOTIFY_DM_ROLE_NAME = os.environ.get('NOTIFY_DM_ROLE_NAME')

intents = discord.Intents.all()
bot = discord.Bot(command_prefix="/", intents=intents)
database = Database(os.environ.get('HOST'), os.environ.get('USER'), os.environ.get('PASSWORD'), os.environ.get('DATABASE'))

@bot.event
async def on_ready():
    notify_homework.start()
    notify_dm_homework.start()

    guild = discord.utils.get(bot.guilds, id=GUILD_IDS[0])
    print(f"{bot.user.name} として {guild.name} にログインしました。")

    notify_channel = discord.utils.get(guild.channels, name=NOTIFY_CHANNEL_NAME)
    if notify_channel is None:
        notify_channel = await guild.create_text_channel(NOTIFY_CHANNEL_NAME)
        print(f"#{notify_channel.name} を作成しました。")
    notify_role = discord.utils.get(guild.roles, name=NOTIFY_ROLE_NAME)
    if notify_role is None:
        notify_role = await guild.create_role(name=NOTIFY_ROLE_NAME)
        print(f"@{notify_role.name} を作成しました。")
    notify_dm_role = discord.utils.get(guild.roles, name=NOTIFY_DM_ROLE_NAME)
    if notify_dm_role is None:
        notify_dm_role = await guild.create_role(name=NOTIFY_DM_ROLE_NAME)
        print(f"@{notify_dm_role.name} を作成しました。")
    await notify_channel.set_permissions(notify_role, read_messages=True)
    await notify_channel.set_permissions(guild.default_role, read_messages=False)
    print(f"#{notify_channel.name} に通知します。")

@bot.slash_command(guild_ids=GUILD_IDS)
async def help(ctx: discord.ApplicationContext):
    """ヘルプを表示します。"""
    embed = Embed(title="ヘルプ", color=Color.green())
    embed.add_field(name="/enable_notify", value="通知を受け取るようになります。", inline=False)
    embed.add_field(name="/disable_notify", value="通知を受け取らないようになります。", inline=False)
    embed.add_field(name="/add_homework", value="課題を追加します。", inline=False)
    embed.add_field(name="/get_homework", value="課題一覧を表示します。", inline=False)
    embed.add_field(name="/get_homework_week", value="1週間以内の課題を表示します。", inline=False)
    embed.add_field(name="/get_homework_month", value="1カ月以内の課題を表示します。", inline=False)
    embed.add_field(name="/get_homework_id", value="課題一覧を表示します。", inline=False)
    embed.add_field(name="/get_homework_week_id", value="1週間以内の課題を表示します。", inline=False)
    embed.add_field(name="/get_homework_month_id", value="1カ月以内の課題を表示します。", inline=False)
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(guild_ids=GUILD_IDS)
async def enable_notify(ctx: discord.ApplicationContext):
    """通知を受け取るようになります。"""
    await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, name=NOTIFY_ROLE_NAME))
    await ctx.respond("通知を受け取るようになりました。", ephemeral=True)

@bot.slash_command(guild_ids=GUILD_IDS)
async def disable_notify(ctx: discord.ApplicationContext):
    """通知を受け取らないようになります。"""
    await ctx.author.remove_roles(discord.utils.get(ctx.guild.roles, name=NOTIFY_ROLE_NAME))
    await ctx.respond("通知を受け取らないようになりました。", ephemeral=True)

@bot.slash_command(guild_ids=GUILD_IDS)
async def enable_notify_dm(ctx: discord.ApplicationContext):
    """DMで課題提出の1時間前に通知を受け取るようになります。"""
    await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, name=NOTIFY_DM_ROLE_NAME))
    await ctx.respond("DMで通知を受け取るようになりました。", ephemeral=True)

@bot.slash_command(guild_ids=GUILD_IDS)
async def disable_notify_dm(ctx: discord.ApplicationContext):
    """DMで課題提出の1時間前に通知を受け取らないようになります。"""
    await ctx.author.remove_roles(discord.utils.get(ctx.guild.roles, name=NOTIFY_DM_ROLE_NAME))
    await ctx.respond("DMで通知を受け取らないようになりました。", ephemeral=True)

@bot.slash_command(guild_ids=GUILD_IDS)
async def add_homework(ctx: discord.ApplicationContext):
    """課題を追加します。"""
    await ctx.send_modal(HWModal(database))

# @param display_id: 課題IDを表示するかどうか
# @param display_description: 課題の説明を表示するかどうか
@bot.slash_command(guild_ids=GUILD_IDS)
async def get_homework(ctx: discord.ApplicationContext, display_id: bool = False, display_description: bool = False):
    """課題一覧を表示します。"""
    await ctx.defer(ephemeral=True)
    homeworks = [homework for homework in database.get_homeworks() if 0 <= get_date_diff(homework[3])]
    devided_homeworks = [homeworks[i:i+10] for i in range(0, len(homeworks), 10)]
    display_pages = []
    for homeworks in devided_homeworks:
        embed = Embed(title="課題一覧", color=Color.green())
        for homework in homeworks:
            id, subject, name, date, description = homework[0], homework[1], homework[2], homework[3], homework[4]
            if display_description:
                if description == "":
                    value = date.strftime("%Y/%m/%d %H:%M")
                else:
                    value = f"{description} ({date.strftime('%Y/%m/%d %H:%M')})"
            else:
                value = date.strftime("%Y/%m/%d %H:%M")
            if display_id:
                embed.add_field(name=f"[{id}] {subject} {name}", value=value, inline=False)
            else:
                embed.add_field(name=f"{subject} {name}", value=value, inline=False)
        display_pages.append(embed)
    paginator = pages.Paginator(pages=display_pages, show_disabled=False)
    await paginator.respond(ctx.interaction, ephemeral=True)

# @param display_id: 課題IDを表示するかどうか
# @param display_description: 課題の説明を表示するかどうか
@bot.slash_command(guild_ids=GUILD_IDS)
async def get_homework_week(ctx: discord.ApplicationContext, display_id: bool = False, display_description: bool = False):
    """1週間以内の課題を表示します。"""
    embed = Embed(title="1週間以内の課題", color=Color.green())
    homeworks = [homework for homework in sorted(database.get_homeworks(), key=lambda x: x[3]) if 0 <= get_date_diff(homework[3]) <= 7]
    for homework in homeworks:
        id, subject, name, date, description = homework[0], homework[1], homework[2], homework[3], homework[4]
        if display_description:
            if description == "":
                value = date.strftime("%Y/%m/%d %H:%M")
            else:
                value = f"{description} ({date.strftime('%Y/%m/%d %H:%M')})"
        else:
            value = date.strftime("%Y/%m/%d %H:%M")
        if display_id:
            embed.add_field(name=f"[{id}] {subject} {name}", value=value, inline=False)
        else:
            embed.add_field(name=f"{subject} {name}", value=value, inline=False)
    await ctx.respond(embed=embed, ephemeral=True)

# @param display_id: 課題IDを表示するかどうか
# @param display_description: 課題の説明を表示するかどうか
@bot.slash_command(guild_ids=GUILD_IDS)
async def get_homework_month(ctx: discord.ApplicationContext, display_id: bool = False, display_description: bool = False):
    """1カ月以内の課題を表示します。"""
    embed = Embed(title="1カ月以内の課題", color=Color.green())
    homeworks = [homework for homework in database.get_homeworks() if 0 <= get_date_diff(homework[3]) <= 30]
    for homework in homeworks:
        id, subject, name, date, description = homework[0], homework[1], homework[2], homework[3], homework[4]
        if display_description:
            if description == "":
                value = date.strftime("%Y/%m/%d %H:%M")
            else:
                value = f"{description} ({date.strftime('%Y/%m/%d %H:%M')})"
        else:
            value = date.strftime("%Y/%m/%d %H:%M")
        if display_id:
            embed.add_field(name=f"[{id}] {subject} {name}", value=value, inline=False)
        else:
            embed.add_field(name=f"{subject} {name}", value=value, inline=False)
    await ctx.respond(embed=embed, ephemeral=True)

# @param id: 課題ID
@bot.slash_command(guild_ids=GUILD_IDS)
async def remove_homework(ctx: discord.ApplicationContext, id: int):
    """課題を削除します。"""
    homework = database.get_homework(id)
    await ctx.send_modal(ConfirmRemoveHWModal(database, homework))

@tasks.loop(seconds=60)
async def notify_homework():
    now = get_jst_now().strftime("%H:%M")
    if now == "07:00" or now == "22:00":
        embed = Embed(title="1週間以内の課題", color=Color.green())
        homeworks = [homework for homework in sorted(database.get_homeworks(), key=lambda x: x[3]) if 0 <= get_date_diff(homework[3]) <= 7]
        if len(homeworks) == 0:
            embed.add_field(name="課題はありません。", value="お疲れ様です。", inline=False)
        else:
            for homework in homeworks:
                id, subject, name, date = homework[0], homework[1], homework[2], homework[3]
                embed.add_field(name=f"{subject} {name}", value=date.strftime("%Y/%m/%d %H:%M"), inline=False)
        guild = discord.utils.get(bot.guilds, id=GUILD_IDS[0])
        channel = discord.utils.get(guild.channels, name=NOTIFY_CHANNEL_NAME)
        notify_role_id = discord.utils.get(channel.guild.roles, name="notify").id
        await channel.send(f"<@&{notify_role_id}>", embed=embed)

@tasks.loop(seconds=60)
async def notify_dm_homework():
    now = get_jst_now().strftime("%H:%M")
    homeworks = [homework for homework in sorted(database.get_homeworks(), key=lambda x: x[3]) if get_date_diff(homework[3]) == 0]
    guild = discord.utils.get(bot.guilds, id=GUILD_IDS[0])
    target_users = [member for member in guild.members if not member.bot and discord.utils.get(member.roles, name=NOTIFY_DM_ROLE_NAME) is not None]
    for homework in homeworks:
        minute_diff = get_minute_diff(homework[3])
        if minute_diff != 60:
            continue
        id, subject, name, date, description = homework[0], homework[1], homework[2], homework[3], homework[4]
        embed = Embed(title="課題の締切が近づいています。", color=Color.green())
        embed.add_field(name=f"{subject} {name}", value=date.strftime("%Y/%m/%d %H:%M"), inline=False)
        if description != "":
            embed.add_field(name="説明", value=description, inline=False)
        for user in target_users:
            channel = await user.create_dm()
            await channel.send(f"<@{user.id}>", embed=embed)

if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
