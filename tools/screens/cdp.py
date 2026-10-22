"""One headless Edge kept open per worker thread, driven over the DevTools protocol (2026-10-14).

Each measure used to start a whole browser (--dump-dom), about 25,000 cold starts for T3b.1d's 10,368 options; with
the antivirus scanning every new profile that held the CPU at 100%. Here a page is a navigation inside a browser that
is already running. Standard library only: a minimal WebSocket client (RFC 6455 text frames, client-masked, fragments
and pings handled) is enough for the DevTools messages.

    evaluate(path, expr, w, h) -> the value of expr (returnByValue) once the page at path has loaded
"""
import atexit
import base64
import json
import os
import socket
import struct
import subprocess
import threading
import time
import urllib.request

_local = threading.local()
_all = []
_lock = threading.Lock()


class _WS:
    def __init__(self, url):
        assert url.startswith("ws://")
        host_port, path = url[5:].split("/", 1)
        host, port = host_port.split(":")
        self.sock = socket.create_connection((host, int(port)), timeout=120)
        key = base64.b64encode(os.urandom(16)).decode()
        req = ("GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
               "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n") % (path, host_port, key)
        self.sock.sendall(req.encode())
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("handshake closed")
            head += chunk
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise ConnectionError("handshake refused: %r" % head[:80])
        self.buf = head.split(b"\r\n\r\n", 1)[1]

    def _read(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("socket closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _send(self, opcode, data):
        head = bytes([0x80 | opcode])
        n = len(data)
        if n < 126:
            head += bytes([0x80 | n])
        elif n < 65536:
            head += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mask = os.urandom(4)
        self.sock.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def send(self, text):
        self._send(0x1, text.encode("utf-8"))

    def recv(self):
        parts = []
        while True:
            b0, b1 = self._read(2)
            fin, op, n = b0 & 0x80, b0 & 0x0F, b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            if b1 & 0x80:   # a server never masks, but read the key if it did
                mk = self._read(4)
                data = bytes(b ^ mk[i % 4] for i, b in enumerate(self._read(n)))
            else:
                data = self._read(n)
            if op == 0x9:
                self._send(0xA, data)
                continue
            if op == 0x8:
                raise ConnectionError("closed by the browser")
            if op in (0x1, 0x0):
                parts.append(data)
                if fin:
                    return b"".join(parts).decode("utf-8")


class Browser:
    def __init__(self, edge, profile):
        os.makedirs(profile, exist_ok=True)
        port_file = os.path.join(profile, "DevToolsActivePort")
        if os.path.exists(port_file):
            os.remove(port_file)
        self.proc = subprocess.Popen([edge, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                                      "--no-first-run", "--disable-extensions", "--disable-background-networking", "--disable-component-update",
                                      "--remote-debugging-port=0", "--user-data-dir=" + profile, "about:blank"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        t0 = time.time()
        while not os.path.exists(port_file):
            if time.time() - t0 > 30:
                raise RuntimeError("Edge gave no DevTools port")
            time.sleep(0.05)
        time.sleep(0.1)
        port = open(port_file, encoding="utf-8").read().split()[0]
        pages = []
        while not pages:
            pages = [t for t in json.load(urllib.request.urlopen("http://127.0.0.1:%s/json/list" % port, timeout=10)) if t.get("type") == "page"]
            if not pages:
                time.sleep(0.1)
        self.ws = _WS(pages[0]["webSocketDebuggerUrl"])
        self.n = 0
        self.call("Page.enable")
        self.size = None

    def call(self, method, params=None, wait_event=None):
        self.n += 1
        mid = self.n
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        got, seen = None, wait_event is None
        while got is None or not seen:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError("%s: %s" % (method, msg["error"]))
                got = msg.get("result", {})
            elif wait_event and msg.get("method") == wait_event:
                seen = True
        return got

    def evaluate(self, path, expr, w, h):
        if self.size != (w, h):
            self.call("Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False})
            self.size = (w, h)
        self.call("Page.navigate", {"url": "file:///" + path.replace("\\", "/")}, wait_event="Page.loadEventFired")
        res = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
        if res.get("exceptionDetails"):
            raise RuntimeError("probe script failed: %s" % res["exceptionDetails"].get("text"))
        return res["result"].get("value")

    def close(self):
        try:   # the browser itself, over DevTools: the process we started may be only its launcher (Edge 155); wait for its
            # answer, or the interpreter exits first and the browser stays (found 2026-10-22)
            self.call("Browser.close")
        except Exception:
            pass
        try:
            self.proc.kill()
        except Exception:
            pass


def evaluate(edge, cache, path, expr, w, h):
    """The value of expr on the page at path, in this thread's browser (started on first use, restarted if it died)."""
    b = getattr(_local, "browser", None)
    # a dead browser shows as a failed connection below, not by its launcher's exit: Edge 155's msedge.exe hands off to the
    # real browser and exits, so polling it started a second browser on the same profile, which gave no port (2026-10-20)
    if b is None:
        # the process id in the name too: thread ids repeat across runs, and a browser left from an earlier run still holds its
        # profile, so the new one gave no port (2026-10-22)
        prof = os.path.join(cache, "cdp-profile-%d-%d" % (os.getpid(), threading.get_ident()))
        try:
            b = Browser(edge, prof)
        except RuntimeError:   # a start that gave no port (seen once mid-build, 2026-10-22, not reproduced): once more, fresh
            b = Browser(edge, prof + "-r%d" % int(time.time()))
        _local.browser = b
        with _lock:
            _all.append(b)
    try:
        return b.evaluate(path, expr, w, h)
    except (ConnectionError, OSError):
        b.close()
        _local.browser = None
        return evaluate(edge, cache, path, expr, w, h)


@atexit.register
def _close_all():
    for b in _all:
        b.close()
