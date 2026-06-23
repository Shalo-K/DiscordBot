###### import #####
import discord
from discord.ext import commands

class BaseMemberUpdateCog(commands.Cog):
    '''
    メンバー情報更新をトリガーとするイベントの共通操作クラス

    Attributes
    ----------
    bot : Bot bot自身のオブジェクト
    '''
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after) -> None:
        if not await self.isTarget(before, after):
            # 処理対象ではない場合、処理終了
            return

        # 処理実行
        await self.mainHandler(before, after)

    async def isTarget(self, before: discord.member, after: discord.member) -> bool:
        raise NotImplementedError("isTarget must be implemented")

    async def mainHandler(self, before: discord.member, after: discord.member) -> None:
        raise NotImplementedError("mainHandler must be implemented")
