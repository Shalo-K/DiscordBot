import datetime

def datetimeFormat(target, format):
    '''
    日時情報をフォーマットする。
    
    Parameters
    ----------
    target : string 変換する日時情報(yyyymmddhhmiss)
    format : string 変換のフォーマット(datetime.strftime)

    Returns
    -------
    result : string 変換後の日時情報

    '''
    result = None
    if (target == "now"):
        dt = datetime.datetime.now()
    else:
        # パラメータチェック
        if (len(target) != 14):
            return result

        # パラメータからdatetime型に変換
        dt = datetime.datetime(
            year = int(target[0:4]),
            month = int(target[4:6]),
            day = int(target[6:8]),
            hour = int(target[8:10]),
            minute = int(target[10:12]),
            second = int(target[12:14]),
            microsecond = 0
        )
    
    result = dt.strftime(format)
    return result