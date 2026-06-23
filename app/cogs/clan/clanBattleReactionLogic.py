###### import #####
import discord
from discord.ext import commands
from cogs.base.baseReactionCog import BaseReactionCog

##### util #####
from util import discordUtil
from util import formatUtil

##### configの読み込み #####
from bot.config import loadAplConst, loadExConf
aplConst = loadAplConst()
exConf = loadExConf("aplConstantsForClanBattle")


class ClanBattleReactionLogic(BaseReactionCog):
    '''
    クランバトル用リアクション処理クラス

    Extends
    ----------
    BaseReactionCog(cogs.base.baseReactionCog)

    Attributes
    ----------
    bot : Bot bot自身のオブジェクト
    '''
    async def isTarget(self, payload: discord.RawReactionClearEvent) -> bool:
            res = False
            
            # リアクション追加以外は対象外
            if not hasattr(payload, "event_type"):
                # リアクション削除時には、event_typeプロパティが存在しない
                return res
            if payload.event_type != "REACTION_ADD":
                return res
            
            # 処理対象のチャンネル名
            targetName = [
                exConf.get("channelName.vote")
                ,exConf.get("channelName.list")
                ,exConf.get("channelName.memory")
                ,exConf.get("channelName.action")
            ]
            
            # メッセージの内容を取得
            messageObject = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

            # 処理対象のチャンネル名に存在有無で返却
            res = messageObject.channel.name in targetName

            return res
        
    async def reactionToBot(self, payload: discord.RawReactionActionEvent):
        '''
        追加されたリアクションに応じた操作を実行

        Parameters
        ----------
        payload : RawReactionActionEvent 追加されたリアクションの情報
        '''
        deleteFlg = False
        
        # メッセージの内容を取得
        messageObject = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

        ##### 凸先アンケート #####
        if (messageObject.channel.name == exConf.get("channelName.vote")):
            deleteFlg = await self.actionChannelVote(payload, messageObject)
            if (deleteFlg):
                await messageObject.delete()

        ##### 凸参加一覧 #####
        elif (messageObject.channel.name == exConf.get("channelName.list")):
            deleteFlg = await self.actionChannelList(payload, messageObject)
            if (deleteFlg):
                await messageObject.delete()

        ###### 凸宣言記録 ######
        elif (messageObject.channel.name == exConf.get("channelName.memory")):
            await self.actionChannelMemory(payload, messageObject)
        
        ##### botメッセージチャンネル ######
        elif (messageObject.channel.name == exConf.get("channelName.action")):
            await self.actionChannelAction(payload, messageObject)

    ##### チャンネルごとのアクションロジック #####
    async def actionChannelVote(self, payload, targetMessage):
        '''
        凸先アンケートチャンネルのリアクション操作

        Parameters
        ----------
        payload       : RawReactionActionEvent 追加されたリアクションの情報
        targetMessage : Message                操作するメッセージの情報

        Returns
        -------
        deleteFlg : メッセージ削除フラグ
        '''
        deleteFlg = False
        embeds = targetMessage.embeds
        userName = payload.member.display_name

        ###### embedあり #####
        if (bool(embeds)):
            ##### 物理/魔法/持越のリアクション #####
            if (payload.emoji.name == aplConst.get("reaction.crossed_swords")
                or payload.emoji.name == aplConst.get("reaction.mage")
                or payload.emoji.name == aplConst.get("reaction.coffee")):
                # リアクションが押された場合、ユーザーを追加/削除する
                if (payload.emoji.name == aplConst.get("reaction.crossed_swords")):
                    # 物理
                    fieldName = exConf.get("embed.physic")
                elif (payload.emoji.name == aplConst.get("reaction.mage")):
                    # 魔法
                    fieldName = exConf.get("embed.magic")
                elif (payload.emoji.name == aplConst.get("reaction.coffee")):
                    # 持越
                    fieldName = exConf.get("embed.re")

                # メッセージを編集してリアクションを解除
                addFlg = await self.editEmbedForEntry(targetMessage, fieldName, userName)
                await targetMessage.remove_reaction(payload.emoji, payload.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(payload.emoji)

            ##### 確定状態変更のリアクション #####
            elif (payload.emoji.name == aplConst.get("reaction.ballot_box_with_check")):
                fieldName = []
                for i in range(0, len(embeds[0].fields)):
                    if (userName in embeds[0].fields[i].value):
                        fieldName.append(embeds[0].fields[i].name)

                if (len(fieldName) == 1):
                    # 編集対象が1つの場合、対象を直接指定して編集
                    await self.editEmbedForCheck(targetMessage, fieldName[0], userName)
                elif (len(fieldName) > 1):
                    # 編集対象が複数ある場合、対象を確認するメッセージを送信
                    content = [payload.member.mention + exConf.get("message.selectCheck")]
                    content.append("||" + aplConst.get("message.channelId") + str(payload.channel_id))
                    content.append(aplConst.get("message.messageId") + str(payload.message_id) + "||")
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
                await targetMessage.remove_reaction(payload.emoji, payload.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(payload.emoji)

            ##### リセットのリアクション #####
            elif (payload.emoji.name == aplConst.get("reaction.wrench")):
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
                await targetMessage.remove_reaction(payload.emoji, payload.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(payload.emoji)

            ##### 予備枠用のリアクション #####
            elif (payload.emoji.name == aplConst.get("reaction.star")):
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
                await targetMessage.remove_reaction(payload.emoji, payload.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(payload.emoji)

        ###### embedなし #####
        else:
            messageText = targetMessage.content.replace("||", "").split("\n")

            ##### 削除リアクション #####
            if (payload.emoji.name == aplConst.get("reaction.x")):
                deleteFlg = True

            ##### 複数の参加がある場合の確定対象再リアクション判定 #####
            elif (exConf.get("message.selectCheck") in messageText[0]):
                if (("~~" in userName) or ("||" in userName)):
                    # 動作上使用できない絵文字が名前に含まれている場合、警告メッセージを送信
                    sent = await targetMessage.reply(content=payload.member.mention + exConf.get("message.alertName"))
                    await sent.add_reaction(aplConst.get("reaction.x"))

                else:
                    channelId = messageText[1].replace(aplConst.get("message.channelId"), "")
                    messageId = messageText[2].replace(aplConst.get("message.messageId"), "")
                    editMessage = await self.bot.get_channel(int(channelId)).fetch_message(int(messageId))
                    if (payload.emoji.name == aplConst.get("reaction.crossed_swords")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.physic"), userName)
                        deleteFlg = True
                    elif (payload.emoji.name == aplConst.get("reaction.mage")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.magic"), userName)
                        deleteFlg = True
                    elif (payload.emoji.name == aplConst.get("reaction.coffee")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.re"), userName)
                        deleteFlg = True
                    elif (payload.emoji.name == aplConst.get("reaction.star")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.spare"), userName)
                        deleteFlg = True

        return deleteFlg


    async def actionChannelList(self, payload, targetMessage):
        '''
        凸参加一覧チャンネルのリアクション操作

        Parameters
        ----------
        payload       : RawReactionActionEvent 追加されたリアクションの情報
        targetMessage : Message                操作するメッセージの情報

        Returns
        -------
        deleteFlg : メッセージ削除フラグ
        '''
        deleteFlg = False
        embeds = targetMessage.embeds
        userName = payload.member.display_name

        ###### embedあり #####
        if (bool(embeds)):
            titleArray = embeds[0].title.split(" ")
            ##### 物理/魔法/持越のリアクション #####
            if (payload.emoji.name == aplConst.get("reaction.crossed_swords")
                or payload.emoji.name == aplConst.get("reaction.mage")
                or payload.emoji.name == aplConst.get("reaction.coffee")):
                # リアクションが押された場合、ユーザーを追加/削除する
                if (payload.emoji.name == aplConst.get("reaction.crossed_swords")):
                    # 物理
                    fieldName = exConf.get("embed.physic")
                elif (payload.emoji.name == aplConst.get("reaction.mage")):
                    # 魔法
                    fieldName = exConf.get("embed.magic")
                elif (payload.emoji.name == aplConst.get("reaction.coffee")):
                    # 持越
                    fieldName = exConf.get("embed.re")

                # メッセージを編集してリアクションを解除
                addFlg = await self.editEmbedForEntry(targetMessage, fieldName, userName)
                await targetMessage.remove_reaction(payload.emoji, payload.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(payload.emoji)

                # ユーザーが追加された場合、凸宣言送信
                if (addFlg):
                    await self.sendAttackMemory(targetMessage.guild, titleArray[0], userName, fieldName)

            ##### 確定状態変更のリアクション #####
            elif (payload.emoji.name == aplConst.get("reaction.ballot_box_with_check")):
                fieldName = []
                for i in range(0, len(embeds[0].fields)):
                    if (userName in embeds[0].fields[i].value):
                        fieldName.append(embeds[0].fields[i].name)

                if (len(fieldName) == 1):
                    # 編集対象が1つの場合、対象を直接指定して編集
                    await self.editEmbedForCheck(targetMessage, fieldName[0], userName)
                elif (len(fieldName) > 1):
                    # 編集対象が複数ある場合、対象を確認するメッセージを送信
                    content = [payload.member.mention + exConf.get("message.selectCheck")]
                    content.append("||" + aplConst.get("message.channelId") + str(payload.channel_id))
                    content.append(aplConst.get("message.messageId") + str(payload.message_id) + "||")
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
                await targetMessage.remove_reaction(payload.emoji, payload.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(payload.emoji)

            ##### リセットのリアクション #####
            elif (payload.emoji.name == aplConst.get("reaction.wrench")):
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
                await targetMessage.remove_reaction(payload.emoji, payload.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(payload.emoji)

            ##### 予備枠用のリアクション #####
            elif (payload.emoji.name == aplConst.get("reaction.star")):
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
                await targetMessage.remove_reaction(payload.emoji, payload.member)

                # botリアクションがない場合は追加する
                await targetMessage.add_reaction(payload.emoji)

                # ユーザーが追加された場合、凸宣言送信
                if (addFlg):
                    # await self.sendAttackMemory(targetMessage.guild, titleArray[0], userName, embeds[0].fields[fieldIndex].name)
                    await self.sendAttackMemory(targetMessage.guild, titleArray[0], userName, exConf.get("embed.spare"))

        ###### embedなし #####
        else:
            messageText = targetMessage.content.replace("||", "").split("\n")

            ##### 削除リアクション #####
            if (payload.emoji.name == aplConst.get("reaction.x")):
                deleteFlg = True

            ##### 複数の参加がある場合の確定対象再リアクション判定 #####
            elif (exConf.get("message.selectCheck") in messageText[0]):
                if (("~~" in userName) or ("||" in userName)):
                    # 動作上使用できない絵文字が名前に含まれている場合、警告メッセージを送信
                    sent = await targetMessage.reply(content=payload.member.mention + exConf.get("message.alertName"))
                    await sent.add_reaction(aplConst.get("reaction.x"))

                else:
                    channelId = messageText[1].replace(aplConst.get("message.channelId"), "")
                    messageId = messageText[2].replace(aplConst.get("message.messageId"), "")
                    editMessage = await self.bot.get_channel(int(channelId)).fetch_message(int(messageId))
                    if (payload.emoji.name == aplConst.get("reaction.crossed_swords")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.physic"), userName)
                        deleteFlg = True
                    elif (payload.emoji.name == aplConst.get("reaction.mage")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.magic"), userName)
                        deleteFlg = True
                    elif (payload.emoji.name == aplConst.get("reaction.coffee")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.re"), userName)
                        deleteFlg = True
                    elif (payload.emoji.name == aplConst.get("reaction.star")):
                        await self.editEmbedForCheck(editMessage, exConf.get("embed.spare"), userName)
                        deleteFlg = True

        return deleteFlg


    async def actionChannelMemory(self, payload, targetMessage):
        '''
        凸宣言記録チャンネルのリアクション操作

        Parameters
        ----------
        payload       : RawReactionActionEvent 追加されたリアクションの情報
        targetMessage : Message                操作するメッセージの情報

        '''
        messageText = targetMessage.content.replace("`", "")

        if (payload.emoji.name == aplConst.get("reaction.x")):
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
            await targetMessage.remove_reaction(payload.emoji, payload.member)


    async def actionChannelAction(self, payload, targetMessage):
        '''
        botメッセージチャンネル(アクション操作用)のリアクション操作

        Parameters
        ----------
        reaction      : RawReactionActionEvent 追加されたリアクションの情報
        targetMessage : Message                操作するメッセージの情報
        '''
        if (payload.emoji.name == aplConst.get("reaction.thumbsup")):
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
                    await targetMessage.remove_reaction(payload.emoji, payload.member)

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
            if (message.author.id == self.bot.user.id):
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
    await bot.add_cog(ClanBattleReactionLogic(bot))
