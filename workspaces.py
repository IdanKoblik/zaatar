#!/usr/bin/env python3

import json
import os
import socket

ICON_ACTIVE = " "
ICON_DEFAULT = " "

def _query():
    path = os.environ.get("NIRI_SOCKET")
    if not path:
        raise RuntimeError("NIRI_SOCKET is not set")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        sock.connect(path)
        sock.sendall(b'"Workspaces"\n')
        reply = json.loads(sock.makefile("rb").readline())
    return reply["Ok"]["Workspaces"]


def text():
    try:
        workspaces = _query()
    except Exception:
        return ICON_DEFAULT
    ordered = sorted(workspaces, key=lambda w: (w.get("output") or "", w.get("idx", 0)))
    icons = [ICON_ACTIVE if w.get("is_active") else ICON_DEFAULT for w in ordered]
    return " ".join(icons) if icons else ICON_DEFAULT


def watch(on_change):
    """Block on a niri event-stream connection, calling on_change() whenever
    the set of workspaces or the active one changes. Raises on connection
    loss so the caller can reconnect."""
    path = os.environ.get("NIRI_SOCKET")
    if not path:
        raise RuntimeError("NIRI_SOCKET is not set")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(path)
        sock.sendall(b'"EventStream"\n')
        stream = sock.makefile("rb")
        stream.readline()  # initial Ok reply
        for raw in stream:
            try:
                event = json.loads(raw)
            except ValueError:
                continue
            if "WorkspacesChanged" in event or "WorkspaceActivated" in event:
                on_change()


if __name__ == "__main__":
    print(text())
