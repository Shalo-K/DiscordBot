###### import #####
import discord
from discord.ext import commands

##### base #####
from cogs.base.baseMessageCog import BaseMessageCog

##### util #####
from util import discordUtil

##### config #####
from bot.config import loadAplConst
aplConst = loadAplConst()

class VoteMessageLogic(BaseMessageCog):
    '''
    メッセージをトリガーとするイベントの処理クラス

    Extends
    ----------
    BaseMessageCog(cogs.base.baseMessageCog)

    Attributes
    ----------
    bot : Bot bot自身のオブジェクト
    '''
    def isTarget(self, message: discord.Message) -> bool:
        # botへのメンションが含まれる場合、True
        return discordUtil.includeMention(message, self.bot.user)

    async def mainHandler(self, message: discord.message) -> None:
        '''
        クラスのメインハンドラ

        Parameters
        ----------
        message : message 処理対象メッセージの情報
        '''
        await self.createReactionListMessage(message)


    ##### 詳細処理 #####
    async def createReactionListMessage(self, message: discord.message) -> None:
        '''
        リアクションを集計するメッセージを作成する。
        作成するメッセージは元のメッセージに対してのリプライになる。

        Parameters
        ----------
        message : message リアクションを集計する対象のメッセージ
        '''
        targetUsers = []
        targetNames = []

        ##### 集計するユーザーの一覧を取得 #####
        # 集計対象メンバーに、ロールに含まれるメンバーを追加
        for role in message.role_mentions:
            targetUsers.extend(role.members)

        # 集計対象メンバーに、直接メンションしているメンバーを追加
        for member in message.mentions:
            targetUsers.append(member)

        # 重複を削除して表示名に置き換え
        targetUsers = list(set(targetUsers))
        targetNames = [user.display_name for user in targetUsers if not (user.bot)]

        # メッセージ文言の作成
        contentArray = [aplConst.get("message.reactionList")]
        contentArray.append(discordUtil.addInline(aplConst.get("message.reactionZero"), 2))
        if (len(targetNames) > 0):
            contentArray.append(aplConst.get("message.noReaction"))
            contentArray.append(discordUtil.addInline(" ".join(targetNames), 2))

        # メッセージを送信
        await message.reply(content="\n".join(contentArray))


##### Cog読み込み時に実行されるメソッド #####
async def setup(bot):
    # Botを渡してインスタンス化し、Botにコグとして登録する
    await bot.add_cog(VoteMessageLogic(bot))
