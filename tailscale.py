#!/usr/bin/env python3

import json
import socket

SOCKETS = ("/run/tailscale/tailscaled.sock", "/var/run/tailscale/tailscaled.sock")
# LocalAPI validates the Host header against this fixed name.
HOST = "local-tailscaled.sock"

def _dechunk(body):
    out = []
    while body:
        size_line, _, rest = body.partition(b"\r\n")
        size = int(size_line.split(b";", 1)[0], 16)
        if size == 0:
            break
        out.append(rest[:size])
        body = rest[size + 2:]  # skip chunk data and trailing \r\n
    return b"".join(out)


def _localapi_get(path):
    last_err = None
    for sock_path in SOCKETS:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(2.0)
                sock.connect(sock_path)
                request = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {HOST}\r\n"
                    "Connection: close\r\n\r\n"
                ).encode()
                sock.sendall(request)

                chunks = []
                while True:
                    data = sock.recv(65536)
                    if not data:
                        break
                    chunks.append(data)
            head, _, body = b"".join(chunks).partition(b"\r\n\r\n")
            if b"transfer-encoding: chunked" in head.lower():
                body = _dechunk(body)
            return body
        except OSError as exc:
            last_err = exc
    raise ConnectionError(f"tailscaled unreachable: {last_err}")


def get_status():
    return json.loads(_localapi_get("/localapi/v0/status"))


def get_ipv4():
    """Return this node's Tailscale IPv4 address, or None if not connected."""
    status = get_status()
    if status.get("BackendState") != "Running":
        return None
    for ip in (status.get("Self") or {}).get("TailscaleIPs") or []:
        if ":" not in ip:  # IPv4
            return ip
    return None


def text():
    try:
        ip = get_ipv4()
    except Exception:
        return "󰛵 disconnected"
    return f"󰛳 {ip}" if ip else "󰛵 offline"


if __name__ == "__main__":
    print(text())
