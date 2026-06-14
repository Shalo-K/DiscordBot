from pathlib import Path
from util.fileController import AplConst, ExtraConfig

# botのルートディレクトリを取得
BASE_DIR = Path(__file__).resolve().parents[1]

def loadAplConst() -> AplConst:
    '''
    アプリケーションで使用する定数をロードしてDictクラスに格納する。
    定数は"conf/aplConstans.json"から取得する。

    Returns
    -------
    ExtraConfig : Dict Config情報
    '''
    return AplConst(str(BASE_DIR))

def loadExConf(fileName) -> ExtraConfig:
    '''
    アプリケーション定数とは異なるjson形式のConfig値をロードしてDictクラスに格納する。
    jsonファイルはconf配下にあるファイル名(拡張子を含まない)を指定する。

    Parameters
    ----------
    fileName : String 取得するjsonファイル名

    Returns
    -------
    ExtraConfig : Dict Config情報
    '''
    return ExtraConfig(str(BASE_DIR), fileName)