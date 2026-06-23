###### import #####
import os
import discord
from discord.ext import commands

##### configの読み込み #####
from bot.config import loadAplConst
aplConst = loadAplConst()

##### BotClientオブジェクト #####
class ClanBattleBot(commands.Bot):
    '''
    Bot本体(Client)のオブジェクト。

    Attributes
    ----------
    eventLogic : EventLogic イベント発生時の処理実装クラス
    '''
    def __init__(self) -> None:
        # botに処理をさせるためのIntentsを指定する
        # あらかじめDeveloper Portalでの権限設定も必要
        intents = discord.Intents(
            guilds           = True
            ,members         = True
            ,messages        = True
            ,reactions       = True
            ,message_content = True
        )

        super().__init__(
            command_prefix    = "/"
            ,case_insensitive = True
            ,help_command     = None
            ,intents          = intents
            ,application_id   = os.getenv("ID_CLIENT")
        )

    async def setup_hook(self) -> None:
        # Cogロード
        cogs = aplConst.get("cogs")
        for c1 in cogs:
            for c2 in cogs[c1]:
                print(f"loading cog:{c1}.{c2}")
                await self.load_extension(f"cogs.{c1}.{c2}")

        # グローバルコマンドとして発行(使用できるまで、最大1時間程度かかる)
        await self.tree.sync()

    ##### イベント処理 #####
    async def on_ready(self) -> None:
        # 起動時に動作する処理
        print("login")

