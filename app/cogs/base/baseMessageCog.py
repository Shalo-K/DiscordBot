###### import #####
import discord
from discord.ext import commands

class BaseMessageCog(commands.Cog):
    '''
    メッセージ操作をトリガーとするイベントの共通操作クラス

    Attributes
    ----------
    bot : Bot bot自身のオブジェクト
    '''
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.message) -> None:
        if message.author.bot:
            # botが作成したメッセージの場合、処理終了
            return

        if not self.isTarget(message):
            # 処理対象ではない場合、処理終了
            return

        # 処理実行
        await self.mainHandler(message)

    def isTarget(self, message: discord.Message) -> bool:
        raise NotImplementedError("isTarget must be implemented")

    async def mainHandler(self, message: discord.message) -> None:
        raise NotImplementedError("mainHandler must be implemented")
