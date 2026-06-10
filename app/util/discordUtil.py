##### import #####
import discord
import datetime

def getChannelByName(guild, channelName):
    '''
    チャンネル名からチャンネルのオブジェクトを取得する。
    取得できない場合はNoneを返却する。

    Parameters
    ----------
    guild       : guild  チャンネルを検索する対象のサーバー
    channelName : string 取得するチャンネルの名前

    Returns
    -------
    channel : channel 検索から取得したチャンネルオブジェクト
    '''
    channels = guild.text_channels
    for channel in channels:
        if (channel.name == channelName):
            # チャンネルが存在した場合、そのチャンネルのオブジェクトを返却
            return guild.get_channel(channel.id)
    
    # 見つからない場合、Noneを返却
    return None

async def getMessageContentFromPayload(client, payload):
    '''
    メッセージのPayloadからメッセージの本文を取得する。

    Parameters
    ----------
    client  : Client  取得を実行するclientのオブジェクト
    payload : Payload 取得する対象のPayloadオブジェクト

    Returns
    -------
    content : String 取得したメッセージの本文
    '''
    messageObject = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    content = messageObject.content
    return content

async def getMessageAuthorIdFromPayload(client, payload):
    '''
    メッセージのPayloadからメッセージ作成者のIDを取得する。

    Parameters
    ----------
    client  : Client  取得を実行するclientのオブジェクト
    payload : Payload 取得する対象のPayloadオブジェクト

    Returns
    -------
    id : int 取得したID
    '''
    messageObject = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    id = messageObject.author.id
    return id

def replaceAllForEmbedText(embed, index, content, beforeString, afterString, separator = None, exclusions = []):
    '''
    embed、インデックス、要素名を指定して、含まれるテキスト内容を全て置換したembedを返却する。
    実際のメッセージ更新は実行しない。
    
    Parameters
    ----------
    embed        : Embed  置換対象のembedオブジェクト
    index        : int    操作対象のインデックス
    content      : string 操作対象の要素名
    beforeString : string 変更前の文字列
    afterString  : string 変更後の文字列
    separator    : string 区切り文字(任意)
    exclusions   : list   除外する文字の一覧(任意)

    Returns
    -------
    Embed : 置換後のembedオブジェクト
    '''
    tempDict = embed.to_dict()

    ##### 区切り文字が指定されている場合 #####
    if (separator is not None):
        # contentを区切り文字で配列化
        contentArray = tempDict["fields"][index][content].split(separator)

        for i, value in enumerate(contentArray):
            # 除外文字を削除
            tempValue = value
            for ex in exclusions:
                tempValue = tempValue.replace(ex, "")
            
            # 削除された状態の文字列に置換対象があるかを確認
            if (beforeString == tempValue):
                # 置換実行(除外文字はそのまま残す)
                contentArray[i] = value.replace(beforeString, afterString)
        
        # 元に戻す
        tempDict["fields"][index][content] = separator.join(contentArray)

    ##### 区切り文字が指定されていない場合 #####
    else:
        # 全置換
        tempDict["fields"][index][content] = tempDict["fields"][index][content].replace(beforeString, afterString)

    # 置換後のembedオブジェクトを返却
    return discord.Embed.from_dict(tempDict)

async def hasReaction(reactions, reactionName = None, user = None):
    '''
    リアクションとユーザー名から、メッセージにリアクションをしているかを判定する。
    リアクションとユーザー名の指定有無は任意

    Parameters
    ----------
    reactions    : List   判定するリアクションのリスト
    reactionName : string 判定するリアクションの名称(任意)
                          指定がない場合は、全てのリアクション(いずれか1つ)を対象とする。
    user         : int    判定するユーザーのID(任意)
                          指定がない場合は、全てのユーザー(いずれか1人)を対象とする。

    Returns
    -------
    result : bool 判定結果
    '''
    result = False

    ###### リアクション自体がない場合 ######
    if (len(reactions) == 0):
        return result

    ###### 絵文字指定なし(どこかにリアクションされていればTrueとする) ######
    if (reactionName is None):
        ##### ユーザー名指定なし #####
        if (user is None):
            result = True
            return result

        ##### ユーザー指定あり #####
        else:
            for r in reactions:
                async for u in r.users():
                    # ユーザーIDの判定
                    if (int(user) == u.id):
                        # 判定終了
                        result = True
                        return result

    ###### 絵文字指定あり ######
    else:
        ##### ユーザー名指定なし #####
        if (user is None):
            for r in reactions:
                if (r.emoji == reactionName):
                    # 判定終了
                    result = True
                    break
            return result

        ##### ユーザー名指定あり #####
        else:
            for r in reactions:
                if (r.emoji == reactionName):
                    # 絵文字の名前が一致する場合、ユーザーを判定
                    async for u in r.users():
                        if (int(user) == u.id):
                            # ユーザー名一致
                            result = True
                            break
                    # ユーザー名判定終了
                    break
            return result

def includeMention(message, user):
    '''
    メッセージとユーザーの情報から、メッセージにユーザーへのメンションが含まれているかを判定する。

    Parameters
    ----------
    message : message 判定する対象のメッセージ
    user    : user    判定するユーザー

    Returns
    -------
    result : bool 判定結果
    '''
    result = False

    ###### 個別メンションの判定 ######
    for member in message.mentions:
        if (member.id == user.id):
            result = True
            return result

    ###### ロールメンションの判定 ######
    for role in message.role_mentions:
        for member in role.members:
            if (member.id == user.id):
                result = True
                return result

    # 該当なし
    return result


async def getMessageFromReply(message, timeout = 5, author = None):
    '''
    指定したメッセージをリプライしているメッセージをlist形式で取得する。
    取得対象の期間は、指定したメッセージが作成された時間を基準に、検索する時間を分単位で指定する。

    Parameters
    ----------
    message : message リプライ元を検索するメッセージ
    timeout : int     取得するメッセージの時間範囲(分)
                        指定がない場合は、5分とする。
    author  : str     取得する対象のユーザー(任意)

    Returns
    -------
    messages : list 取得したメッセージのリスト
                    取得されなかった場合は空の状態で返却される。
    '''
    messages = []
    timeFrom = message.created_at
    timeTo = timeFrom + datetime.timedelta(minutes = int(timeout))

    async for m in message.channel.history(before = timeTo, after = timeFrom, oldest_first = True):
        if (m.reference) is not None:
            if (m.reference.message_id == message.id):
                # リプライで参照しているメッセージIDと一致
                if author is None:
                    # ユーザー指定なし
                    messages.append(m)
                else:
                    # ユーザー指定あり
                    if (m.author == author):
                        # 指定されたユーザーと一致
                        messages.append(m)

    return messages


def getEmbedFieldIndexByName(embed, findName):
    '''
    指定したname要素と一致するembed.fieldのインデックスを返却する。
    該当のインデックスが存在しない場合、Noneを返却する。

    Parameters
    ----------
    embed     : Embed  : 検索するembedの本体
    findName  : String : 検索するname要素の名称

    Returns
    -------
    result : int 取得したインデックス
    '''
    result = None

    for i in range(0, len(embed.fields)):
        if (embed.fields[i].name == findName):
            result = i
            break
    
    return result
