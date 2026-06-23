###### import #####
import discord
from discord.ext import commands

##### base #####
from cogs.base.baseReactionCog import BaseReactionCog

##### util #####
from util import discordUtil

##### config #####
from bot.config import loadAplConst
aplConst = loadAplConst()

class VoteReactionLogic(BaseReactionCog):
    '''
    リアクション操作イベントの処理クラス

    Extends
    ----------
    BaseReactionCog(cogs.base.baseReactionCog)

    Attributes
    ----------
    bot : Bot bot自身のオブジェクト
    '''
    async def isTarget(self, payload: discord.RawReactionClearEvent) -> bool:
        res = False

        # 集計形式のbotメッセージか、botからメンションされているメッセージが対象
        # メッセージの取得
        reactionMessage = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

        if (aplConst.get("message.reactionList") in reactionMessage.content):
            # 集計形式のbotメッセージ
            res = True
        elif (discordUtil.includeMention(reactionMessage, self.bot.user)):
            # botへのメンションが含まれている場合
            res = True
        
        return res

    async def reactionToBot(self, payload: discord.RawReactionClearEvent) -> None:
        '''
        bot自身が作成したメッセージに対するリアクションの実行ロジック

        Parameters
        ----------
        payload : RawReactionActionEvent 実行されたリアクションの情報
        '''
        reactionMessage = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

        if (aplConst.get("message.reactionList") in reactionMessage.content):
            # リアクション一覧の集計
            await self.editReactionListMessage(reactionMessage)

    async def reactionElseBot(self, payload: discord.RawReactionClearEvent) -> None:
        '''
        bot以外が作成したメッセージに対するリアクションの実行ロジック

        Parameters
        ----------
        payload : RawReactionActionEvent 実行されたリアクションの情報
        '''
        reactionMessage = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

        if (discordUtil.includeMention(reactionMessage, self.bot.user)):
            # メッセージにbotへのメンションが含まれる場合
            botMessages = await discordUtil.getMessageFromReply(message= reactionMessage, author= self.bot.user)
            # 対象のメッセージにbotのリアクションを追加
            for bm in botMessages:
                if not (payload.emoji.is_custom_emoji()):
                    await bm.add_reaction(payload.emoji)
                    await reactionMessage.remove_reaction(payload.emoji, payload.member)
                    # 集計のメッセージ内容を更新
                    await self.editReactionListMessage(bm)


    ##### 詳細処理 #####
    async def editReactionListMessage(self, message):
        '''
        リアクションを集計するメッセージを編集する。

        Parameters
        ----------
        message : message リアクションが実行されたメッセージ
        '''
        targetUsers = []
        targetNames = []
        reactionUsers = []
        message = await message.fetch()

        ##### 集計するユーザーの一覧を取得 #####
        messageReference = message.reference
        if messageReference is not None:
            fetchMessage = await message.channel.fetch_message(messageReference.message_id)

        # 集計対象メンバーに、ロールに含まれるメンバーを追加
        for role in fetchMessage.role_mentions:
            targetUsers.extend(role.members)

        # 集計対象メンバーに、直接メンションしているメンバーを追加
        for member in fetchMessage.mentions:
            targetUsers.append(member)

        # 重複を削除して表示名に置き換え
        targetUsers = list(set(targetUsers))
        targetUsers = [user for user in targetUsers if not (user.bot)]
        targetNames = [user.display_name for user in targetUsers]
        
        ##### メッセージ文言の作成 #####
        contentArray = [aplConst.get("message.reactionList")]

        # カスタム絵文字でないリアクションを取得
        reactions = [r for r in message.reactions if not (r.is_custom_emoji())]
        if (len(reactions) > 0):
            # 集計対象のリアクションが存在する場合
            for r in reactions:
                # リアクションの一覧を取得
                reactionUsers = [u.display_name async for u in r.users() if not (u.bot)]

                contentArray.append(str(r.emoji))
                if (len(reactionUsers) > 0):
                    contentArray.append(discordUtil.addInline(" ".join(reactionUsers), 2))
                else:
                    contentArray.append(discordUtil.addInline(aplConst.get("message.reactionZero"), 2))

                # 集計対象メンバーから、リアクションを追加しているユーザーを削除する
                for ru in reactionUsers:
                    for tn in targetNames:
                        if (tn == ru):
                            targetNames.remove(ru)
                            break
        else:
            # 集計対象のリアクションが存在しない場合
            contentArray.append(discordUtil.addInline(aplConst.get("message.reactionNoDefined"), 2))

        if (len(targetUsers) > 0):
            # どこにもリアクションしていないユーザー
            contentArray.append(aplConst.get("message.noReaction"))
            if (len(targetNames) > 0):
                contentArray.append(discordUtil.addInline(" ".join(targetNames), 2))
            else:
                contentArray.append(discordUtil.addInline(aplConst.get("message.reactionZero"), 2))

        # メッセージを編集
        await message.edit(content="\n".join(contentArray))

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
        contentArray.append(discordUtil.addInline(aplConst.get("message.reactionNoDefined"), 2))
        if (len(targetNames) > 0):
            contentArray.append(aplConst.get("message.noReaction"))
            contentArray.append(discordUtil.addInline(" ".join(targetNames), 2))

        # メッセージを送信
        await message.reply(content="\n".join(contentArray))


##### Cog読み込み時に実行されるメソッド #####
async def setup(bot):
    # Botを渡してインスタンス化し、Botにコグとして登録する
    await bot.add_cog(VoteReactionLogic(bot))
