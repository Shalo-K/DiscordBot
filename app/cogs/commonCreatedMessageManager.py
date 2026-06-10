###### import #####
import os
import discord
from discord.ext import commands

##### util #####
from util import discordUtil
from util.fileController import AplConst

##### configの読み込み #####
aplPath = os.getcwd()
aplConst = AplConst(aplPath)


class CommonCreatedMessageManager(commands.Cog):
    '''
    メッセージ作成時の操作定義クラス

    Attributes
    ----------
    bot : Bot bot自身のオブジェクト
    '''
    def __init__(self, bot):
        self.bot = bot
    
    async def mainLogic(self, message: discord.message):
        '''
        クラスのメインロジック

        Parameters
        ----------
        message : message 作成されたメッセージの情報

        Returns
        -------
        endFlag : 処理終了フラグ
        '''
        endFlag = False

        if (discordUtil.includeMention(message, self.bot.user)):
            ##### メッセージにbotへのメンションが含まれる場合 #####
            # リアクション一覧の作成
            await self.createReactionListMessage(message)

        ##### 終了 #####
        return endFlag

    async def createReactionListMessage(self, message: discord.message):
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
        contentArray.append("```リアクションが未登録です```")
        if (len(targetNames) > 0):
            contentArray.append(aplConst.get("message.noReaction"))
            contentArray.append("```" + " ".join(targetNames) + "```")

        # メッセージを送信
        await message.reply(content="\n".join(contentArray))


##### Cog読み込み時に実行されるメソッド #####
async def setup(bot):
    # Botを渡してインスタンス化し、Botにコグとして登録する
    await bot.add_cog(CommonCreatedMessageManager(bot))
