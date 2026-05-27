def round_seconds(seconds: float | int | None) -> float | None:
    if seconds is None:
        return None
    return round(float(seconds), 3)
