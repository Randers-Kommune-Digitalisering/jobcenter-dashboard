import math


def decimalMinutesToStr(minutes):
    if not minutes:
        return "—"
    if math.isnan(minutes):
        return "—"
    if isinstance(minutes, str):
        minutes = float(minutes)
    minutesOut = int(minutes)

    def minutesText(x):
        return "minut" if x == 1 else "minutter"
    secondsOut = (minutes - int(minutes)) * 60
    if minutesOut == 0:
        return f"__{secondsOut:.0f}__ sekunder"
    if secondsOut == 0:
        return f"__{minutesOut}__ {minutesText(minutesOut)}"
    return f"__{minutesOut}__ {minutesText(minutesOut)} og __{secondsOut:.0f}__ sekunder"


def format_timedelta_in_danish(td):
    days = td.days
    seconds = td.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    parts = []
    if days > 0:
        parts.append(f"{days} dage")
    if hours > 0:
        parts.append(f"{hours} timer")
    if minutes > 0:
        parts.append(f"{minutes} minutter")
    if seconds > 0:
        parts.append(f"{seconds} sekunder")

    return ", ".join(parts)


def timedelta_to_minutes(td_str):
    try:
        parts = td_str.split(", ")
        total_minutes = 0
        for part in parts:
            if "dage" in part:
                total_minutes += int(part.split()[0]) * 60 * 24
            elif "timer" in part:
                total_minutes += int(part.split()[0]) * 60
            elif "minutter" in part:
                total_minutes += int(part.split()[0]) * 1
            elif "sekunder" in part:
                total_minutes += int(part.split()[0]) / 60
        return total_minutes
    except ValueError:
        return None
