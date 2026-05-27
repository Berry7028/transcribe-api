def round_seconds(seconds: float | int | None) -> float | None:
    """レスポンスで扱う秒数をミリ秒精度に丸める。"""

    if seconds is None:
        return None
    return round(float(seconds), 3)
