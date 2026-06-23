###### import #####
import discord
from discord.ext import commands
from cogs.base.baseMemberUpdateCog import BaseMemberUpdateCog

##### util #####
from util import discordUtil

##### configの読み込み #####
from bot.config import loadAplConst, loadExConf
aplConst = loadAplConst()
exConf = loadExConf("aplConstantsForClanBattle")

class ClanBattleMemberUpdateLogic(BaseMemberUpdateCog):
    '''
    クランバトル用リアクション処理クラス

    Extends
    ----------
    BaseMemberUpdateCog(cogs.base.baseMemberUpdateCog)

    Attributes
    ----------
    bot : Bot bot自身のオブジェクト
    '''
    async def isTarget(self, before: discord.member, after: discord.member) -> bool:
            res = False
            
            # 表示名が変更となった場合が対象
            if (before.display_name != after.display_name):
                res = True

            return res

    async def mainHandler(self, before: discord.member, after: discord.member) -> None:
        '''
        クラスのメインハンドラ

        Parameters
        ----------
        before : 変更前のユーザ情報
        after  : 変更後のユーザ情報
        '''
        await self.changeNickInEmbeds(before, after)


    async def changeNickInEmbeds(self, before: discord.Member, after: discord.Member):
        '''
        embedのリストに登録されているユーザ名を変更する。
        ユーザ名はユーザ情報のオブジェクトから取得する

        Parameters
        ----------
        before : 変更前のユーザ情報
        after  : 変更後のユーザ情報
        '''
        # 変更確認メッセージの送信チャンネル取得
        sendChannel = discordUtil.getChannelByName(before.guild, exConf.get("channelName.action"))

        # 本文の要素
        content = [before.mention + exConf.get("message.changeNameAction")]
        content.append(exConf.get("message.changeBefore") + before.display_name)
        content.append(exConf.get("message.changeAfter") + after.display_name)

        # 送信
        sent = await sendChannel.send(content="\n".join(content))

        # 操作用リアクション
        await sent.add_reaction(aplConst.get("reaction.thumbsup"))


##### Cog読み込み時に実行されるメソッド #####
async def setup(bot):
    # Botを渡してインスタンス化し、Botにコグとして登録する
    await bot.add_cog(ClanBattleMemberUpdateLogic(bot))
