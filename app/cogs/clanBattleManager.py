###### import #####
import datetime
import enum
import os
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands

##### util #####
from util import discordUtil
from util import formatUtil

##### configの読み込み #####
from bot.confing import loadAplConst, loadExConf
aplPath = Path(__file__).resolve().parents[1]
aplConst = loadAplConst()
exConf = loadExConf("aplConstantsForClanBattle")


##### コマンドパラメータ用のEnum #####
class ChannelListEnum(enum.Enum):
    vote = exConf.get("channelName.vote")
    list = exConf.get("channelName.list")

##### cogのクラス定義 #####
class ClanBattleCommandManager(commands.Cog):
    '''
    クランバトル用コマンド定義クラス

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
                    outPath = aplPath + "/tmp/memory_" + target + ".csv"
                    await interaction.followup.send(content="全てのデータを取得完了。csv出力します。", ephemeral= True)
                    with open(outPath, "w", encoding='utf-8') as f:
                        f.write("\n".join(getMessages))
                    
                    # 完了メッセージ
                    await interaction.user.send(file= discord.File(outPath))
                    resultMessage = baseTime.strftime("%Y/%m/%d") + "の凸情報を取得しました。"
                    # 送信後にファイル削除
                    os.remove(outPath)

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



##### リアクション操作 #####
class ClanBattleReactionManager(commands.Cog):
    '''
    クランバトル用リアクション操作定義クラス

    Attributes
    ----------
    bot : Bot bot自身のオブジェクト
    '''
    def __init__(self, bot):
        self.bot = bot
    
    async def reactionAdd(self, message: discord.RawReactionActionEvent):
        '''
        追加されたリアクションに応じた操作を実行

        Parameters
        ----------
        message : RawReactionActionEvent 追加されたリアクションの情報

        Returns
        -------
        endFlag : 処理終了フラグ
        '''
        endFlag = False
        deleteFlg = False
        
        if (message.user_id != int(os.getenv("ID_CLIENT"))):
            # リアクションを実行したユーザがbot自身でない場合のアクション
            # メッセージの内容を取得
            messageObject = await self.bot.get_channel(message.channel_id).fetch_message(message.message_id)

            if (messageObject.author.id == int(os.getenv("ID_CLIENT"))):
                # bot自身が作成したメッセージに対するリアクションの場合のアクション
                ##### 凸先アンケート #####
                if (messageObject.channel.name == exConf.get("channelName.vote")):
                    deleteFlg = await self.actionChannelVote(message, messageObject)
                    if (deleteFlg):
                        await messageObject.delete()

                    # 後続のリアクション判定を実施しない
                    endFlag = True

                ##### 凸参加一覧 #####
                elif (messageObject.channel.name == exConf.get("channelName.list")):
                    deleteFlg = await self.actionChannelList(message, messageObject)
                    if (deleteFlg):
                        await messageObject.delete()

                    # 後続のリアクション判定を実施しない
                    endFlag = True

                ###### 凸宣言記録 ######
                elif (messageObject.channel.name == exConf.get("channelName.memory")):
                    await self.actionChannelMemory(message, messageObject)

                    # 後続のリアクション判定を実施しない
                    endFlag = True
                
                ##### botメッセージチャンネル ######
                elif (messageObject.channel.name == exConf.get("channelName.action")):
                    await self.actionChannelAction(message, messageObject)

                    # 後続のリアクション判定を実施しない
                    endFlag = True
        
        # 判定終了
        return endFlag


    ##### チャンネルごとのアクションロジック #####
    async def actionChannelVote(self, reaction, targetMessage):
        '''
        凸先アンケートチャンネルのリアクション操作

        Parameters
        ----------
        reaction      : RawReactionActionEvent 追加されたリアクションの情報
        targetMessage : Message                操作するメッセージの情報

        Returns
        -------
        deleteFlg : メッセージ削除フラグ
        '''
        deleteFlg = False
        embeds = targetMessage.embeds
        userName = reaction.member.display_name

        ###### embedあり #####
        if (bool(embeds)):
            ##### 物理/魔法/持越のリアクション #####
            if (reaction.emoji.name == aplConst.get("reaction.crossed_swords")
                or reaction.emoji.name == aplConst.get("reaction.mage")
                or reaction.emoji.name == aplConst.get("reaction.coffee")):
                # リアクションが押された場合、ユーザーを追加/削除する
                if (reaction.emoji.name == aplConst.get("reaction.crossed_swords")):
                    # 物理
                    fieldName = exConf.get("embed.physic")
                elif (reaction.emoji.name == aplConst.get("reaction.mage")):
                    # 魔法
                    fieldName = exConf.get("embed.magic")
                elif (reaction.emoji.name == aplConst.get("reaction.coffee")):
                    # 持越
                    fieldName = exConf.get("embed.re")

                # メッセージを編集してリアクションを解除
                addFlg = await self.editEmbedForEntry(targetMessage, fieldName, userName)
                await targetMessage.remove_reaction(reaction.emoji, reaction.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(reaction.emoji)

            ##### 確定状態変更のリアクション #####
            elif (reaction.emoji.name == aplConst.get("reaction.ballot_box_with_check")):
                fieldName = []
                for i in range(0, len(embeds[0].fields)):
                    if (userName in embeds[0].fields[i].value):
                        fieldName.append(embeds[0].fields[i].name)

                if (len(fieldName) == 1):
                    # 編集対象が1つの場合、対象を直接指定して編集
                    await self.editEmbedForCheck(targetMessage, fieldName[0], userName)
                elif (len(fieldName) > 1):
                    # 編集対象が複数ある場合、対象を確認するメッセージを送信
                    content = [reaction.member.mention + exConf.get("message.selectCheck")]
                    content.append("||" + aplConst.get("message.channelId") + str(reaction.channel_id))
                    content.append(aplConst.get("message.messageId") + str(reaction.message_id) + "||")
                    sent = await targetMessage.reply(content = "\n".join(content))
                    
                    for n in fieldName:
                        # フィールド名に応じたリアクションを追加
                        if (n == exConf.get("embed.physic")):
                            await sent.add_reaction(aplConst.get("reaction.crossed_swords"))
                        elif (n == exConf.get("embed.magic")):
                            await sent.add_reaction(aplConst.get("reaction.mage"))
                        elif (n == exConf.get("embed.re")):
                            await sent.add_reaction(aplConst.get("reaction.coffee"))
                        elif (n == exConf.get("embed.spare")):
                            await sent.add_reaction(aplConst.get("reaction.star"))
                    await sent.add_reaction(exConf.get("reaction.x"))

                # リアクションを解除
                await targetMessage.remove_reaction(reaction.emoji, reaction.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(reaction.emoji)

            ##### リセットのリアクション #####
            elif (reaction.emoji.name == aplConst.get("reaction.wrench")):
                content = embeds[0].to_dict()
                for i in range(0, len(embeds[0].fields)):
                    content["fields"][i]["value"] = ""
                    if (content["fields"][i]["name"] == exConf.get("embed.spare")):
                        # 予備枠の削除
                        del content["fields"][i]

                # メッセージを編集
                embed = discord.Embed.from_dict(content)
                await targetMessage.edit(embed=embed)
            
                # リアクションを解除
                await targetMessage.remove_reaction(reaction.emoji, reaction.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(reaction.emoji)

            ##### 予備枠用のリアクション #####
            elif (reaction.emoji.name == aplConst.get("reaction.star")):
                # 予備用枠の追加と削除
                addFlg = True
                for i in range(0, len(embeds[0].fields)):
                    if (embeds[0].fields[i].name == exConf.get("embed.spare")):
                        addFlg = False
                        break

                if (addFlg):
                    # 予備用枠がない場合、fieldを追加
                    embeds[0].add_field(name= exConf.get("embed.spare"), value= "", inline= False)
                    content = embeds[0].to_dict()
                    embed = discord.Embed.from_dict(content)
                    await targetMessage.edit(embed=embed)

                # ユーザーの編集
                addFlg = await self.editEmbedForEntry(targetMessage, exConf.get("embed.spare"), userName)

                # リアクションを解除
                await targetMessage.remove_reaction(reaction.emoji, reaction.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(reaction.emoji)

        ###### embedなし #####
        else:
            messageText = targetMessage.content.replace("||", "").split("\n")

            ##### 削除リアクション #####
            if (reaction.emoji.name == aplConst.get("reaction.x")):
                deleteFlg = True

            ##### 複数の参加がある場合の確定対象再リアクション判定 #####
            elif (exConf.get("message.selectCheck") in messageText[0]):
                if (("~~" in userName) or ("||" in userName)):
                    # 動作上使用できない絵文字が名前に含まれている場合、警告メッセージを送信
                    sent = await targetMessage.reply(content=reaction.member.mention + exConf.get("message.alertName"))
                    await sent.add_reaction(aplConst.get("reaction.x"))

                else:
                    channelId = messageText[1].replace(aplConst.get("message.channelId"), "")
                    messageId = messageText[2].replace(aplConst.get("message.messageId"), "")
                    editMessage = await self.bot.get_channel(int(channelId)).fetch_message(int(messageId))
                    if (reaction.emoji.name == aplConst.get("reaction.crossed_swords")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.physic"), userName)
                        deleteFlg = True
                    elif (reaction.emoji.name == aplConst.get("reaction.mage")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.magic"), userName)
                        deleteFlg = True
                    elif (reaction.emoji.name == aplConst.get("reaction.coffee")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.re"), userName)
                        deleteFlg = True
                    elif (reaction.emoji.name == aplConst.get("reaction.star")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.spare"), userName)
                        deleteFlg = True

        return deleteFlg


    async def actionChannelList(self, reaction, targetMessage):
        '''
        凸参加一覧チャンネルのリアクション操作

        Parameters
        ----------
        reaction      : RawReactionActionEvent 追加されたリアクションの情報
        targetMessage : Message                操作するメッセージの情報

        Returns
        -------
        deleteFlg : メッセージ削除フラグ
        '''
        deleteFlg = False
        embeds = targetMessage.embeds
        userName = reaction.member.display_name

        ###### embedあり #####
        if (bool(embeds)):
            titleArray = embeds[0].title.split(" ")
            ##### 物理/魔法/持越のリアクション #####
            if (reaction.emoji.name == aplConst.get("reaction.crossed_swords")
                or reaction.emoji.name == aplConst.get("reaction.mage")
                or reaction.emoji.name == aplConst.get("reaction.coffee")):
                # リアクションが押された場合、ユーザーを追加/削除する
                if (reaction.emoji.name == aplConst.get("reaction.crossed_swords")):
                    # 物理
                    fieldName = exConf.get("embed.physic")
                elif (reaction.emoji.name == aplConst.get("reaction.mage")):
                    # 魔法
                    fieldName = exConf.get("embed.magic")
                elif (reaction.emoji.name == aplConst.get("reaction.coffee")):
                    # 持越
                    fieldName = exConf.get("embed.re")

                # メッセージを編集してリアクションを解除
                addFlg = await self.editEmbedForEntry(targetMessage, fieldName, userName)
                await targetMessage.remove_reaction(reaction.emoji, reaction.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(reaction.emoji)

                # ユーザーが追加された場合、凸宣言送信
                if (addFlg):
                    await self.sendAttackMemory(targetMessage.guild, titleArray[0], userName, fieldName)

            ##### 確定状態変更のリアクション #####
            elif (reaction.emoji.name == aplConst.get("reaction.ballot_box_with_check")):
                fieldName = []
                for i in range(0, len(embeds[0].fields)):
                    if (userName in embeds[0].fields[i].value):
                        fieldName.append(embeds[0].fields[i].name)

                if (len(fieldName) == 1):
                    # 編集対象が1つの場合、対象を直接指定して編集
                    await self.editEmbedForCheck(targetMessage, fieldName[0], userName)
                elif (len(fieldName) > 1):
                    # 編集対象が複数ある場合、対象を確認するメッセージを送信
                    content = [reaction.member.mention + exConf.get("message.selectCheck")]
                    content.append("||" + aplConst.get("message.channelId") + str(reaction.channel_id))
                    content.append(aplConst.get("message.messageId") + str(reaction.message_id) + "||")
                    sent = await targetMessage.reply(content = "\n".join(content))

                    for n in fieldName:
                        # フィールド名に応じたリアクションを追加
                        if (n == exConf.get("embed.physic")):
                            await sent.add_reaction(aplConst.get("reaction.crossed_swords"))
                        elif (n == exConf.get("embed.magic")):
                            await sent.add_reaction(aplConst.get("reaction.mage"))
                        elif (n == exConf.get("embed.re")):
                            await sent.add_reaction(aplConst.get("reaction.coffee"))
                        elif (n == exConf.get("embed.spare")):
                            await sent.add_reaction(aplConst.get("reaction.star"))
                    await sent.add_reaction(aplConst.get("reaction.x"))

                # リアクションを解除
                await targetMessage.remove_reaction(reaction.emoji, reaction.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(reaction.emoji)

            ##### リセットのリアクション #####
            elif (reaction.emoji.name == aplConst.get("reaction.wrench")):
                content = embeds[0].to_dict()
                for i in range(0, len(embeds[0].fields)):
                    content["fields"][i]["value"] = ""
                    if (content["fields"][i]["name"] == exConf.get("embed.spare")):
                        # 予備枠の削除
                        del content["fields"][i]

                # メッセージを編集
                embed = discord.Embed.from_dict(content)
                await targetMessage.edit(embed=embed)
            
                # リアクションを解除
                await targetMessage.remove_reaction(reaction.emoji, reaction.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(reaction.emoji)

            ##### 予備枠用のリアクション #####
            elif (reaction.emoji.name == aplConst.get("reaction.star")):
                # 予備用枠の追加と削除
                addFlg = True
                for i in range(0, len(embeds[0].fields)):
                    if (embeds[0].fields[i].name == exConf.get("embed.spare")):
                        addFlg = False
                        break

                if (addFlg):
                    # 予備用枠がない場合、fieldを追加
                    embeds[0].add_field(name= exConf.get("embed.spare"), value= "", inline= False)
                    content = embeds[0].to_dict()
                    embed = discord.Embed.from_dict(content)
                    await targetMessage.edit(embed=embed)

                # ユーザーの編集
                addFlg = await self.editEmbedForEntry(targetMessage, exConf.get("embed.spare"), userName)

                # リアクションを解除
                await targetMessage.remove_reaction(reaction.emoji, reaction.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(reaction.emoji)

                # ユーザーが追加された場合、凸宣言送信
                if (addFlg):
                    # await self.sendAttackMemory(targetMessage.guild, titleArray[0], userName, embeds[0].fields[fieldIndex].name)
                    await self.sendAttackMemory(targetMessage.guild, titleArray[0], userName, exConf.get("embed.spare"))

        ###### embedなし #####
        else:
            messageText = targetMessage.content.replace("||", "").split("\n")

            ##### 削除リアクション #####
            if (reaction.emoji.name == aplConst.get("reaction.x")):
                deleteFlg = True

            ##### 複数の参加がある場合の確定対象再リアクション判定 #####
            elif (exConf.get("message.selectCheck") in messageText[0]):
                if (("~~" in userName) or ("||" in userName)):
                    # 動作上使用できない絵文字が名前に含まれている場合、警告メッセージを送信
                    sent = await targetMessage.reply(content=reaction.member.mention + exConf.get("message.alertName"))
                    await sent.add_reaction(aplConst.get("reaction.x"))

                else:
                    channelId = messageText[1].replace(aplConst.get("message.channelId"), "")
                    messageId = messageText[2].replace(aplConst.get("message.messageId"), "")
                    editMessage = await self.bot.get_channel(int(channelId)).fetch_message(int(messageId))
                    if (reaction.emoji.name == aplConst.get("reaction.crossed_swords")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.physic"), userName)
                        deleteFlg = True
                    elif (reaction.emoji.name == aplConst.get("reaction.mage")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.magic"), userName)
                        deleteFlg = True
                    elif (reaction.emoji.name == aplConst.get("reaction.coffee")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.re"), userName)
                        deleteFlg = True
                    elif (reaction.emoji.name == aplConst.get("reaction.star")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.spare"), userName)
                        deleteFlg = True

        return deleteFlg


    async def actionChannelMemory(self, reaction, targetMessage):
        '''
        凸宣言記録チャンネルのリアクション操作

        Parameters
        ----------
        reaction      : RawReactionActionEvent 追加されたリアクションの情報
        targetMessage : Message                操作するメッセージの情報

        '''
        messageText = targetMessage.content.replace("`", "")

        if (reaction.emoji.name == aplConst.get("reaction.x")):
            # 凸宣言のキャンセル
            # 既にキャンセル済でないかを確認
            completeFlg = await discordUtil.hasReaction(targetMessage.reactions
                                                        ,aplConst.get("reaction.ballot_box_with_check")
                                                        ,targetMessage.author.id)

            if not (completeFlg):
                await targetMessage.reply(content="キャンセルされました")
                await targetMessage.edit(content="~~" + messageText + "~~")
                await targetMessage.add_reaction(aplConst.get("reaction.ballot_box_with_check"))
            
            # リアクション解除
            await targetMessage.remove_reaction(reaction.emoji, reaction.member)


    async def actionChannelAction(self, reaction, targetMessage):
        '''
        botメッセージチャンネル(アクション操作用)のリアクション操作

        Parameters
        ----------
        reaction      : RawReactionActionEvent 追加されたリアクションの情報
        targetMessage : Message                操作するメッセージの情報
        '''
        if (reaction.emoji.name == aplConst.get("reaction.thumbsup")):
            # アクション実行リアクション
            messageText = targetMessage.content.split("\n")
            if (exConf.get("message.changeNameAction") in messageText[0]):
                # 名前変更操作
                deleteFlg = False
                retryFlg = False

                # 前回の失敗リアクションがある場合、解除する
                retryFlg = await discordUtil.hasReaction(targetMessage.reactions
                                                         ,aplConst.get("reaction.thinking")
                                                         ,targetMessage.author.id)
                if (retryFlg):
                    await targetMessage.remove_reaction(aplConst.get("reaction.thinking"), targetMessage.author)

                beforeName = messageText[1].replace(exConf.get("message.changeBefore"), "")
                afterName = messageText[2].replace(exConf.get("message.changeAfter"), "")

                # 検索対象のチャンネル
                channelVote = discordUtil.getChannelByName(targetMessage.guild, exConf.get("channelName.vote"))
                channelList = discordUtil.getChannelByName(targetMessage.guild, exConf.get("channelName.list"))
                
                # 置換実行
                try:
                    await self.editEmbedForRename(channelVote, beforeName, afterName)
                    await self.editEmbedForRename(channelList, beforeName, afterName)
                    
                    # 完了メッセージ送信
                    content = [exConf.get("message.changeNameDone")]
                    content.append(messageText[1])
                    content.append(messageText[2])
                    await targetMessage.channel.send(content="\n".join(content))

                    deleteFlg = True
                except Exception as e:
                    # 置換に失敗した場合、リアクションを追加
                    await targetMessage.add_reaction(aplConst.get("reaction.thinking"))
                    await targetMessage.remove_reaction(reaction.emoji, reaction.member)

                # 処理終了後にメッセージを削除する
                if (deleteFlg):
                    await targetMessage.delete()


    ##### アクション内の詳細動作 #####
    async def editEmbedForEntry(self, message, fieldName, userName):
        '''
        メッセージのembedを編集し、凸参加情報を変更する。

        Parameters
        ----------
        message   : Message 編集するメッセージの情報
        fieldName : string  編集するembedのfieldにつけられた名称
        userName  : string  参加情報を変更するユーザー

        Returns
        -------
        addFlg : 追加実行フラグ
        '''
        addFlg = True
        embeds = message.embeds
        content = embeds[0].to_dict()

        # 対象のfield確定
        fieldIndex = discordUtil.getEmbedFieldIndexByName(embeds[0], fieldName)
        
        if (fieldIndex is not None):
            fieldValueArray = embeds[0].fields[fieldIndex].value.split("\n")

            for value in fieldValueArray:
                if (userName == value.replace("~~", "")):
                    # ユーザー削除
                    addFlg = False
                    fieldValueArray.remove(value)
                    if ((fieldName == exConf.get("embed.spare")) and (len(fieldValueArray) == 0)):
                        # 予備枠が空となる場合、フィールドごと削除する
                        del content["fields"][fieldIndex]
                    else:
                        content["fields"][fieldIndex]["value"] = "\n".join(fieldValueArray)
                    break
            
            if (addFlg):
                # ユーザー追加
                fieldValueArray.append(userName)
                content["fields"][fieldIndex]["value"] = "\n".join(fieldValueArray)

            # メッセージを編集
            embed = discord.Embed.from_dict(content)
            await message.edit(embed=embed)

        return addFlg


    async def editEmbedForCheck(self, message, fieldName, userName):
        '''
        メッセージのembedを編集し、凸完了情報を変更する。

        Parameters
        ----------
        message   : Message 編集するメッセージの情報
        fieldName : string  編集するembedのfieldにつけられた名称
        userName  : string  情報を変更するユーザー
        '''
        embeds = message.embeds
        content = embeds[0].to_dict()

        # 対象のfield確定
        fieldIndex = discordUtil.getEmbedFieldIndexByName(embeds[0], fieldName)

        if (fieldIndex is not None):
            fieldValueArray = embeds[0].fields[fieldIndex].value.split("\n")

            for index, value in enumerate(fieldValueArray):
                if (userName == value):
                    # 確定
                    fieldValueArray[index] = ("~~" + userName + "~~")
                    break
                elif (("~~" + userName + "~~") == value):
                    # 確定の解除
                    fieldValueArray[index] = userName
                    break

            # メッセージを編集
            content["fields"][fieldIndex]["value"] = "\n".join(fieldValueArray)
            embed = discord.Embed.from_dict(content)
            await message.edit(embed=embed)


    async def sendAttackMemory(self, guild, boss, user, attribute):
        '''
        凸宣言を送信する。

        Parameters
        ----------
        guild     : guild  送信するサーバ
        boss      : string 宣言対象のボス
        user      : string 宣言するユーザー
        attribute : string 攻撃の詳細
        '''
        # チャンネル検索
        sendChannel = discordUtil.getChannelByName(guild, exConf.get("channelName.memory"))
        
        # 送信する情報を作成
        logTime = formatUtil.datetimeFormat("now", "%Y/%m/%d %H:%M:%S")
        nameInfo = boss + " " + user + " " + attribute

        # 送信してリアクションを作成
        sent = await sendChannel.send(content="```" + logTime + " " + nameInfo + "```")
        await sent.add_reaction(aplConst.get("reaction.x"))


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


##### ユーザ名変更操作 ######
class ClanBattleNameManager(commands.Cog):
    '''
    クランバトル用名前変更定義クラス

    Attributes
    ----------
    bot : Bot bot自身のオブジェクト
    '''
    def __init__(self, bot):
        self.bot = bot

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
    await bot.add_cog(ClanBattleReactionManager(bot))
    await bot.add_cog(ClanBattleCommandManager(bot))
    await bot.add_cog(ClanBattleNameManager(bot))
