#!/usr/bin/env python3

from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Jerusalem")


def get_date():
    """Current local time, matching the old Waybar clock format."""
    return datetime.now(TZ).strftime("%d/%m/%Y - %H:%M:%S")


def text():
    return get_date()


if __name__ == "__main__":
    print(text())
