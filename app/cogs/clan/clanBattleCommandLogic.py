###### import #####
import datetime
import enum
import os
from pathlib import Path
import tempfile
import discord
from discord import app_commands
from discord.ext import commands

##### util #####
from util import discordUtil

##### configの読み込み #####
from bot.config import loadAplConst, loadExConf
aplConst = loadAplConst()
exConf = loadExConf("aplConstantsForClanBattle")

##### csv用tmpディレクトリ ##### 
tmpPath = Path(tempfile.gettempdir())


##### コマンドパラメータ用のEnum #####
class ChannelListEnum(enum.Enum):
    vote = exConf.get("channelName.vote")
    list = exConf.get("channelName.list")

class ClanBattleCommandLogic(commands.Cog):
    '''
    クランバトル用コマンド処理クラス

    Attributes
    ----------
    bot : Bot bot自身のオブジェクト
    '''
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name = "messageset", description = "操作用メッセージ作成")
    async def messageset(self, interaction: discord.Interaction, channel: ChannelListEnum):
        '''
        クランバトル操作用のメッセージを作成する。

        Parameters
        ----------
        channel : ChannelListEnum メッセージを作成する対象のチャンネル
        '''
        completeFlag = False
        await interaction.response.defer(ephemeral=True)
        # チャンネル取得
        channelObject = discordUtil.getChannelByName(interaction.guild, channel.value)
        if channelObject is None:
            await interaction.followup.send("指定されたチャンネル(" + channel.value + ")が存在しません。", ephemeral=True)
        else:
            if (channel.value == exConf.get("channelName.vote")):
                for i in range(1,6):
                    # embed作成
                    embed = discord.Embed(title= str(i) + exConf.get("embed.vote"))
                    embed.add_field(name= exConf.get("embed.physic"), value= "", inline= False)
                    embed.add_field(name= exConf.get("embed.magic"), value= "", inline= False)
                    embed.add_field(name= exConf.get("embed.re"), value= "", inline= False)

                    # 凸先アンケートにリアクション付きでメッセージを作成
                    sent = await channelObject.send(embed=embed)
                    await sent.add_reaction(aplConst.get("reaction.crossed_swords"))
                    await sent.add_reaction(aplConst.get("reaction.mage"))
                    await sent.add_reaction(aplConst.get("reaction.coffee"))
                    await sent.add_reaction(aplConst.get("reaction.star"))
                    await sent.add_reaction(aplConst.get("reaction.ballot_box_with_check"))
                    await sent.add_reaction(aplConst.get("reaction.wrench"))
                completeFlag = True

            elif (channel.value == exConf.get("channelName.list")):
                for i in range(1,6):
                    # embed作成
                    embed = discord.Embed(title= str(i) + exConf.get("embed.list"))
                    embed.add_field(name= exConf.get("embed.physic"), value= "", inline= False)
                    embed.add_field(name= exConf.get("embed.magic"), value= "", inline= False)
                    embed.add_field(name= exConf.get("embed.re"), value= "", inline= False)

                    # 凸参加一覧にリアクション付きでメッセージを作成
                    sent = await channelObject.send(embed=embed)
                    await sent.add_reaction(aplConst.get("reaction.crossed_swords"))
                    await sent.add_reaction(aplConst.get("reaction.mage"))
                    await sent.add_reaction(aplConst.get("reaction.coffee"))
                    await sent.add_reaction(aplConst.get("reaction.star"))
                    await sent.add_reaction(aplConst.get("reaction.ballot_box_with_check"))
                    await sent.add_reaction(aplConst.get("reaction.wrench"))
                completeFlag = True
            
            if (completeFlag):
                await interaction.followup.send("メッセージを作成しました。(" + channel.value + ")", ephemeral=True)
            else:
                await interaction.followup.send("メッセージの作成に失敗しました。(" + channel.value + ")", ephemeral=True)


    @app_commands.command(name = "changename", description = "リスト内ユーザ名の編集")
    async def changename(self, interaction: discord.Interaction, before: str, after: str):
        '''
        クランバトル操作用のリストに含まれる名前を変更する。
        
        Parameters
        ----------
        before : String 変更前の名前
        after  : String 変更後の名前
        '''
        completeFlag = False
        await interaction.response.defer(ephemeral=True)

        # 対象のチャンネル取得
        channelVote = discordUtil.getChannelByName(interaction.guild, exConf.get("channelName.vote"))
        channelList = discordUtil.getChannelByName(interaction.guild, exConf.get("channelName.list"))
        channelLog = discordUtil.getChannelByName(interaction.guild, exConf.get("channelName.action"))

        # 置換実行
        try:
            await self.editEmbedForRename(channelVote, before, after)
            await self.editEmbedForRename(channelList, before, after)
            completeFlag = True
        except Exception as e:
            # 置換に失敗した場合、リアクションを追加
            content = ["名前の変更に失敗しました。"]
            content.append(exConf.get("message.changeBefore") + before)
            content.append(exConf.get("message.changeAfter") + after)
            await interaction.followup.send(content = "\n".join(content))

        # 処理終了後にメッセージを送信する
        if (completeFlag):
            content = [exConf.get("message.changeNameDone")]
            content.append(exConf.get("message.changeBefore") + before)
            content.append(exConf.get("message.changeAfter") + after)
            await interaction.followup.send(content = "\n".join(content))
            await channelLog.send(content = "\n".join(content))


    @app_commands.command(name = "l", description = "凸履歴を1日分取得する")
    async def getLogMemory(self, interaction: discord.Interaction, target: str):
        '''
        凸履歴を1日分取得する。
        取得結果はコマンド実行者にDMで送信する。
        
        Parameters
        ----------
        target : String 取得する日付(yyyymmdd)
        '''
        # DMでは実行できないように制御
        if (interaction.guild_id == None):
            await interaction.response.send_message(content= "このコマンドはDMでは使用できません。", ephemeral= True)

        # パラメータチェック
        elif (len(target) != 8):
            await interaction.response.send_message(content="パラメータに不備があります。yyyymmdd形式で指定してください。", ephemeral=True)

        else:
            resultMessage = ""
            await interaction.response.defer(ephemeral=True)
            try:
                # 対象の日付を変換
                baseTime = datetime.datetime(
                    year = int(target[0:4]),
                    month = int(target[4:6]),
                    day = int(target[6:8]),
                    hour = 5,
                    minute = 0,
                    second = 0,
                    microsecond = 0
                )

                # 対象チャンネルを取得
                ch = discordUtil.getChannelByName(interaction.guild, exConf.get("channelName.memory"))
                if (ch == None):
                    resultMessage = exConf.get("channelName.memory") + "チャンネルを取得できませんでした。"
                
                else:
                    # メッセージを取得してDMで送信
                    getMessages = []
                    for i in range(0, 25):
                        timeFrom = baseTime + datetime.timedelta(hours= i)
                        timeTo = timeFrom + datetime.timedelta(hours= 1)
                        getMessages.extend([m.content.replace("`", "").replace(" ", ",") async for m in ch.history(before = timeTo, after = timeFrom, oldest_first = True) if "`" in m.content])
                        if (i != 0 and i % 3 == 0):
                            await interaction.followup.send(
                                content = (timeFrom + datetime.timedelta(hours= -3)).strftime("%Y/%m/%d %H") + "～" + timeFrom.strftime("%H") + "時台の凸情報を取得しました。",
                                ephemeral = True
                            )
                    
                    # csv出力
                    timeStamp = datetime.datetime.now().strftime("_%Y%m%d%H%M%S")
                    fileName = "memory_" + target + timeStamp + ".csv"
                    outPath = tmpPath / fileName
                    await interaction.followup.send(content="全てのデータを取得完了。csv出力します。", ephemeral= True)
                    try:
                        with open(outPath, "w", encoding='utf-8') as f:
                            f.write("\n".join(getMessages))
                        
                        # 完了メッセージ
                        await interaction.user.send(file= discord.File(outPath))
                        resultMessage = baseTime.strftime("%Y/%m/%d") + "の凸情報を取得しました。"
                    
                    except:
                        resultMessage = "csvの出力に失敗しました。"

                    finally:
                        # 送信後にファイル削除
                        outPath.unlink()

            except ValueError as ve:
                # 日付情報の変換エラー
                resultMessage = "パラメータに不備があります。yyyymmdd形式で指定してください。"
            
            finally:
                # 処理終了後のメッセージ送信(共通)
                await interaction.followup.send(content= resultMessage, ephemeral= True)


    async def editEmbedForRename(self, channel, beforeName, afterName):
        '''
        メッセージのembedを編集し、既に登録されている名前を変更する。

        Parameters
        ----------
        channel    : Channel 編集するメッセージを検索するチャンネル
        beforeName : string  編集するembedのインデックス
        afterName  : string  参加情報を変更するユーザー
        '''
        async for message in channel.history(limit = 100):
            if (message.author.id == int(os.getenv("ID_CLIENT"))):
                editFlag = False
                embeds = message.embeds
                if (bool(embeds)):
                    # bot自身が生成したメッセージかつembedが使用されている場合、変更操作を実行
                    for i in range(0, len(embeds[0].fields)):
                        # メッセージ内の対象単語を全て置換
                        tempString = embeds[0].fields[i].value
                        embeds[0] = discordUtil.replaceAllForEmbedText(embeds[0], i, "value", beforeName, afterName, "\n", ["~", "|"])
                        
                        if (tempString != embeds[0].fields[i].value):
                            editFlag = True

                    if (editFlag):
                        # 置換の前後を比較し、差分があった場合のみ変更を確定
                        await message.edit(embed=embeds[0])


##### Cog読み込み時に実行されるメソッド #####
async def setup(bot):
    # Botを渡してインスタンス化し、Botにコグとして登録する
    await bot.add_cog(ClanBattleCommandLogic(bot))
