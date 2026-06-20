#!/usr/bin/env python3

import threading
import time

import cputemp
import date
import gputemp
import memory
import pulseaudio
import tailscale
import uptime
import workspaces

RIGHT = (uptime, tailscale, cputemp, gputemp, memory)

# Gap rendered between adjacent right-side modules (they share one pill, so the
# separator is what makes them breathe like waybar's spaced-out modules).
SEP = "    "

def _safe(module):
    """Return module.text(), swallowing any error so one bad module can't
    take the whole line down."""
    try:
        return module.text()
    except Exception:
        return ""


def line():
    left = _safe(workspaces)
    center = _safe(date)
    right = SEP.join(s for s in (_safe(m) for m in RIGHT) if s)
    return f"%{{#d6d5d5}}  Void\t%{{#d6d5d5}}{center}\t%{{#d6d5d5}}{right}"


def _watch_workspaces(wake):
    """Reconnecting loop that flips `wake` on every niri workspace change so
    the bar redraws immediately instead of waiting for the next-second tick."""
    while True:
        try:
            workspaces.watch(wake.set)
        except Exception:
            time.sleep(1)  # niri gone or socket dropped; retry


def main():
    wake = threading.Event()
    threading.Thread(target=_watch_workspaces, args=(wake,), daemon=True).start()
    while True:
        wake.clear()
        print(line(), flush=True)
        # Wake on the whole-second tick (clock/modules) or sooner on a switch.
        wake.wait(1 - time.time() % 1)


if __name__ == "__main__":
    main()
