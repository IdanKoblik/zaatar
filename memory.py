#!/usr/bin/env python3

MEMINFO = "/proc/meminfo"


def _read_meminfo():
    fields = {}
    with open(MEMINFO) as fh:
        for line in fh:
            key, _, rest = line.partition(":")
            fields[key] = int(rest.strip().split()[0])  # value is in kB
    return fields


def get_memory():
    """Return (used_gib, total_gib) using the kernel's MemAvailable."""
    info = _read_meminfo()
    total_kb = info["MemTotal"]
    available_kb = info.get("MemAvailable", info["MemFree"])
    used_kb = total_kb - available_kb
    gib = 1024 * 1024
    return used_kb / gib, total_kb / gib


def text():
    used, total = get_memory()
    return f"  {used:.1f}G/{total:.1f}G"


if __name__ == "__main__":
    print(text())
