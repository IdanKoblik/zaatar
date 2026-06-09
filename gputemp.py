#!/usr/bin/env python3

import ctypes

NVML_SUCCESS = 0
NVML_TEMPERATURE_GPU = 0
_LIB_NAMES = ("libnvidia-ml.so.1", "libnvidia-ml.so")


def _load():
    for name in _LIB_NAMES:
        try:
            return ctypes.CDLL(name)
        except OSError:
            continue
    return None


def get_gpu_temp(index=0):
    """Return GPU ``index`` temperature in Celsius, or None if unavailable."""
    lib = _load()
    if lib is None:
        return None

    if lib.nvmlInit_v2() != NVML_SUCCESS:
        return None
    try:
        handle = ctypes.c_void_p()
        if lib.nvmlDeviceGetHandleByIndex_v2(index, ctypes.byref(handle)) != NVML_SUCCESS:
            return None
        temp = ctypes.c_uint()
        rc = lib.nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU, ctypes.byref(temp))
        return temp.value if rc == NVML_SUCCESS else None
    finally:
        lib.nvmlShutdown()


def text():
    temp = get_gpu_temp()
    return f"󰢮 {temp}°C" if temp is not None else "󰢮 N/A"


if __name__ == "__main__":
    print(text())
