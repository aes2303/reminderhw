import discord, pytz
from datetime import datetime, timedelta, timezone
from discord.ui import Modal, InputText
from discord import Color, Embed, InputTextStyle, Interaction

from database import Database


def get_jst_now() -> datetime:
    return datetime.now(timezone(timedelta(hours=+9), 'JST'))

def jst_localize(dt: datetime) -> datetime:
    return pytz.timezone('Asia/Tokyo').localize(dt)

def get_date_diff(dt: datetime) -> int:
    return (jst_localize(dt) - get_jst_now()).days

def get_minute_diff(dt: datetime) -> int:
    return (jst_localize(dt) - get_jst_now()).seconds // 60

class HWModal(Modal):
    def __init__(self, database):
        super().__init__(title="課題登録")
        self.database = database

        self.subject = InputText(label="教科名", min_length=1, max_length=16)
        self.add_item(self.subject)

        self.name = InputText(label="課題名", min_length=1, max_length=16)
        self.add_item(self.name)

        self.date = InputText(label="締切(YYYY/MM/DD/HH/mm)", min_length=16, max_length=16)
        self.add_item(self.date)

        self.description = InputText(label="課題の説明", min_length=1, max_length=100, required=False, style=InputTextStyle.long)
        self.add_item(self.description)

    async def callback(self, interaction: Interaction):
        try:
            date = datetime.strptime(self.date.value, "%Y/%m/%d/%H/%M")
        except ValueError:
            await interaction.response.send_message(content="日付の形式が正しくありません。", ephemeral=True)
            self.stop()
            return
        date = jst_localize(date)

        if date < get_jst_now():
            await interaction.response.send_message(content="締切が過ぎています。", ephemeral=True)
            self.stop()
            return

        description = self.description.value.replace("\n", " ")
        self.database.add_homework(self.subject.value, self.name.value, date, description)

        embed = Embed(title="課題を追加しました。", description=f"教科名: {self.subject.value}\n課題名: {self.name.value}\n締切: {date.strftime('%Y/%m/%d %H:%M')}\n説明: {self.description.value}", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
        self.stop()

class ConfirmRemoveHWModal(Modal):
    def __init__(self, database: Database, homework: list[id, str, str, str]):
        super().__init__(title="課題削除の承認")
        self.database = database
        self.homework = homework

        self.add_item(InputText(label=f"{self.homework[1]}の{self.homework[2]}を削除しますか？", placeholder="入力しなくてOK", required=False))

    async def callback(self, interaction: Interaction):
        self.database.delete_homework(self.homework[0])
        embed = Embed(title="課題を削除しました。", description=f"教科名: {self.homework[1]}\n課題名: {self.homework[2]}\n締切: {self.homework[3].strftime('%Y/%m/%d %H:%M')}\n説明: {self.homework[4]}", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
        self.stop()

