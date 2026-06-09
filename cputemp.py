#!/usr/bin/env python3

import glob
import os

HWMON_GLOB = "/sys/class/hwmon/hwmon*"
PREFERRED_NAMES = ("coretemp", "k10temp", "zenpower", "acpitz")


def _hwmon_by_name():
    found = {}
    for path in glob.glob(HWMON_GLOB):
        try:
            with open(os.path.join(path, "name")) as fh:
                found[fh.read().strip()] = path
        except OSError:
            continue
    return found


def _sensor_path():
    sensors = _hwmon_by_name()
    for name in PREFERRED_NAMES:
        if name in sensors:
            return sensors[name]
    return next(iter(sensors.values()), None)


def get_cpu_temp():
    """Return the package temperature in whole degrees Celsius, or None."""
    base = _sensor_path()
    if base is None:
        return None
    with open(os.path.join(base, "temp1_input")) as fh:
        return round(int(fh.read().strip()) / 1000)


def text():
    temp = get_cpu_temp()
    return f" {temp}°C" if temp is not None else " N/A"


if __name__ == "__main__":
    print(text())
