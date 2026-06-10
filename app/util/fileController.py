import json

def input_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def output_json(filename, obj):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=4, ensure_ascii=False)

class AplConst:
    '''
    アプリケーションで使用する定数を格納するクラス
    定数は"conf/aplConstans.json"から取得する。

    Attributes
    ----------
    aplConst : AttrDict 定数を格納するオブジェクト
    '''
    def __init__(self, aplPath):
        self.aplConst = input_json(aplPath + "/conf/aplConstants.json")
    
    def get(self, key):
        '''
        指定された名前に紐づく定数(String)を返却する。
        見つからない場合はNoneを返却する。

        Parameters
        ----------
        key : String 取得する定数の名称

        Returns
        -------
        value : String 取得した定数の結果
        '''
        value = self.aplConst
        keys = key.split(".")
        for name in keys:
            if (value == None):
                break
            value = value.get(name)
        return value


class ExtraConfig:
    '''
    アプリケーション定数とは異なるjson形式のConfig値を取得するクラス。
    jsonファイルはconf配下にあるファイル名(拡張子を含まない)を指定する。

    Attributes
    ----------
    exConf : Config値を格納するオブジェクト
    '''
    def __init__(self, aplPath, fileName):
        self.exConf = input_json(aplPath + "/conf/" + fileName + ".json")
    
    def get(self, key):
        '''
        指定された名前に紐づく定数(String)を返却する。
        見つからない場合はNoneを返却する。

        Parameters
        ----------
        key : String 取得する定数の名称

        Returns
        -------
        value : String 取得した定数の結果
        '''
        value = self.exConf
        keys = key.split(".")
        for name in keys:
            if (value == None):
                break
            value = value.get(name)
        return value
