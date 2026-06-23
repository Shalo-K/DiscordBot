###### import #####
import os
import asyncio
from bot.client import ClanBattleBot
from bot.config import loadAplConst

##### configの読み込み #####
aplConst = loadAplConst()

##### Cog一覧取得　 #####
cogs = aplConst.get("cogs")

# Botのインスタンス化および起動処理。
async def main() -> None:
    # トークン読込(.envファイルで定義)
    token = os.getenv("TOKEN")
    if not token:
        raise RuntimeError("TOKEN is not set")

    # Botログイン
    bot = ClanBattleBot()
    async with bot:
        await bot.start(token)

if __name__ == '__main__':
    # 起動
    asyncio.run(main())
