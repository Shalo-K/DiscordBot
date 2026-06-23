###### import #####
import discord
from discord.ext import commands

##### util #####
from util import discordUtil

class BaseReactionCog(commands.Cog):
    '''
    リアクション操作をトリガーとするイベントの共通操作クラス

    Attributes
    ----------
    bot : Bot bot自身のオブジェクト
    '''
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionClearEvent) -> None:
        if self.isBotReaction(payload):
            # bot自体からのリアクションであった場合、処理終了
            return

        if not await self.isTarget(payload):
            # 処理対象ではない場合、処理終了
            return

        if await self.isBotMessage(payload):
            # botが作成したメッセージの場合
            await self.reactionToBot(payload)
        else:
            # bot以外が作成したメッセージの場合
            await self.reactionElseBot(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionClearEvent) -> None:
        if self.isBotReaction(payload):
            # bot自体からのリアクションであった場合、処理終了
            return

        if not await self.isTarget(payload):
            # 処理対象ではない場合、処理終了
            return

        if await self.isBotMessage(payload):
            # botが作成したメッセージの場合
            await self.reactionToBot(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload: discord.RawReactionClearEvent) -> None:
        if not await self.isTarget(payload):
            # 処理対象ではない場合、処理終了
            return

        if await self.isBotMessage(payload):
            # botが作成したメッセージの場合
            await self.reactionToBot(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload: discord.RawReactionClearEvent) -> None:
        if not await self.isTarget(payload):
            # 処理対象ではない場合、処理終了
            return

        if await self.isBotMessage(payload):
            # botが作成したメッセージの場合
            await self.reactionToBot(payload)

    async def isTarget(self, payload: discord.RawReactionClearEvent) -> bool:
        raise NotImplementedError("isTarget must be implemented")

    def isBotReaction(self, payload: discord.RawReactionClearEvent) -> bool:
        return payload.user_id == self.bot.user.id

    async def isBotMessage(self, payload: discord.RawReactionClearEvent) -> bool:
        return await discordUtil.getMessageAuthorIdFromPayload(self.bot, payload) == self.bot.user.id

    async def reactionToBot(self, payload: discord.RawReactionClearEvent) -> None:
        raise NotImplementedError("reactionToBot must be implemented")

    async def reactionElseBot(self, payload: discord.RawReactionClearEvent) -> None:
        raise NotImplementedError("reactionElseBot must be implemented")
