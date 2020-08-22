def tz_UTC(tz:int):
    """
    设定时区
    :param tz: 与 UTC 时区的时差
    :raise ValueError: 超出时区范围
    """
    if tz <= -12 or tz >= 12:
        raise ValueError()
    from datetime import timezone, timedelta
    return timezone(timedelta(hours=tz))