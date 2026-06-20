#!/usr/bin/env python3

UPTIME = "/proc/uptime"

def get_uptime_seconds():
    with open(UPTIME) as fh:
        return float(fh.read().split()[0])


def _humanise(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes = seconds // 60

    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    # mirror `uptime -p`: always show minutes when nothing bigger exists
    if minutes or not parts:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    return "up " + ", ".join(parts)


def get_uptime():
    return _humanise(get_uptime_seconds())


def text():
    return f"{get_uptime()}"


if __name__ == "__main__":
    print(text())
