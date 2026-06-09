#!/usr/bin/env python3
"""Volume module — default sink volume/mute via libpulse (ctypes).

Binds the PulseAudio client library directly (PipeWire's pulse shim answers
it the same), so there is no pactl/wpctl subprocess. Every bound function
declares argtypes/restype — without them ctypes narrows the 64-bit context
and mainloop pointers to int and the process segfaults.
"""

import ctypes

PA_VOLUME_NORM = 0x10000
PA_CHANNELS_MAX = 32
PA_CONTEXT_READY = 4
PA_CONTEXT_FAILED = 5
PA_CONTEXT_TERMINATED = 6

_lib = ctypes.CDLL("libpulse.so.0")

c_void_p = ctypes.c_void_p
c_int = ctypes.c_int
c_uint32 = ctypes.c_uint32
c_uint8 = ctypes.c_uint8
c_char_p = ctypes.c_char_p


class _SampleSpec(ctypes.Structure):
    _fields_ = [("format", c_int), ("rate", c_uint32), ("channels", c_uint8)]


class _ChannelMap(ctypes.Structure):
    _fields_ = [("channels", c_uint8), ("map", c_int * PA_CHANNELS_MAX)]


class _CVolume(ctypes.Structure):
    _fields_ = [("channels", c_uint8), ("values", c_uint32 * PA_CHANNELS_MAX)]


class _SinkInfo(ctypes.Structure):
    # Only the prefix up to `mute` needs to be laid out correctly.
    _fields_ = [
        ("name", c_char_p),
        ("index", c_uint32),
        ("description", c_char_p),
        ("sample_spec", _SampleSpec),
        ("channel_map", _ChannelMap),
        ("owner_module", c_uint32),
        ("volume", _CVolume),
        ("mute", c_int),
    ]


class _ServerInfo(ctypes.Structure):
    _fields_ = [
        ("user_name", c_char_p),
        ("host_name", c_char_p),
        ("server_version", c_char_p),
        ("server_name", c_char_p),
        ("sample_spec", _SampleSpec),
        ("default_sink_name", c_char_p),
        ("default_source_name", c_char_p),
    ]


_SINK_CB = ctypes.CFUNCTYPE(None, c_void_p, ctypes.POINTER(_SinkInfo), c_int, c_void_p)
_SERVER_CB = ctypes.CFUNCTYPE(None, c_void_p, ctypes.POINTER(_ServerInfo), c_void_p)
_STATE_CB = ctypes.CFUNCTYPE(None, c_void_p, c_void_p)


def _bind(name, restype, argtypes):
    fn = getattr(_lib, name)
    fn.restype = restype
    fn.argtypes = argtypes
    return fn


pa_mainloop_new = _bind("pa_mainloop_new", c_void_p, [])
pa_mainloop_free = _bind("pa_mainloop_free", None, [c_void_p])
pa_mainloop_get_api = _bind("pa_mainloop_get_api", c_void_p, [c_void_p])
pa_mainloop_iterate = _bind("pa_mainloop_iterate", c_int, [c_void_p, c_int, c_void_p])
pa_context_new = _bind("pa_context_new", c_void_p, [c_void_p, c_char_p])
pa_context_connect = _bind("pa_context_connect", c_int, [c_void_p, c_char_p, c_int, c_void_p])
pa_context_disconnect = _bind("pa_context_disconnect", None, [c_void_p])
pa_context_unref = _bind("pa_context_unref", None, [c_void_p])
pa_context_get_state = _bind("pa_context_get_state", c_int, [c_void_p])
pa_context_set_state_callback = _bind(
    "pa_context_set_state_callback", None, [c_void_p, _STATE_CB, c_void_p]
)
pa_context_get_server_info = _bind(
    "pa_context_get_server_info", c_void_p, [c_void_p, _SERVER_CB, c_void_p]
)
pa_context_get_sink_info_by_name = _bind(
    "pa_context_get_sink_info_by_name", c_void_p, [c_void_p, c_char_p, _SINK_CB, c_void_p]
)
pa_operation_unref = _bind("pa_operation_unref", None, [c_void_p])


def _avg_percent(cvolume):
    n = cvolume.channels
    if n == 0:
        return 0
    total = sum(cvolume.values[i] for i in range(n))
    return round(total / n * 100 / PA_VOLUME_NORM)


def get_volume():
    """Return (volume_percent, muted_bool) for the default sink, or None."""
    result = {}

    mainloop = pa_mainloop_new()
    api = pa_mainloop_get_api(mainloop)
    ctx = pa_context_new(api, b"zaatar")

    @_SINK_CB
    def on_sink(_c, info_ptr, eol, _u):
        if eol == 0 and info_ptr:
            info = info_ptr.contents
            result["volume"] = _avg_percent(info.volume)
            result["muted"] = bool(info.mute)

    @_SERVER_CB
    def on_server(_c, info_ptr, _u):
        sink = info_ptr.contents.default_sink_name
        if sink:
            pa_operation_unref(pa_context_get_sink_info_by_name(ctx, sink, on_sink, None))

    @_STATE_CB
    def on_state(_c, _u):
        if pa_context_get_state(ctx) == PA_CONTEXT_READY:
            pa_operation_unref(pa_context_get_server_info(ctx, on_server, None))

    pa_context_set_state_callback(ctx, on_state, None)
    if pa_context_connect(ctx, None, 0, None) < 0:
        pa_context_unref(ctx)
        pa_mainloop_free(mainloop)
        return None

    try:
        for _ in range(2000):  # ~2s safety bound
            pa_mainloop_iterate(mainloop, 1, None)
            if "volume" in result:
                break
            if pa_context_get_state(ctx) in (PA_CONTEXT_FAILED, PA_CONTEXT_TERMINATED):
                break
    finally:
        pa_context_disconnect(ctx)
        pa_context_unref(ctx)
        pa_mainloop_free(mainloop)

    if "volume" not in result:
        return None
    return result["volume"], result["muted"]


def _icon(volume):
    ramp = ["", "", " "]
    return ramp[min(len(ramp) - 1, volume * len(ramp) // 101)]


def text():
    info = get_volume()
    if info is None:
        return " "
    volume, muted = info
    if muted:
        return ""
    return f"%{{#ea999c}}{_icon(volume)} {volume}%"

if __name__ == "__main__":
    print(text())
