"""A small MCP client for local (stdio) servers. Standard library only.

    client = McpClient("tickets", [sys.executable, "tickets_server.py"])
    client.start()                 # launch the server, shake hands, list its tools
    client.tools                   # [{"name", "description", "inputSchema", ...}, ...]
    client.call("get_ticket", {"id": 2})  # -> (text, is_error)
    client.close()

What the MCP spec says about stdio (modelcontextprotocol.io, versions 2025-11-25 and 2026-07-28):
  - the client launches the server as a subprocess;
  - messages are JSON-RPC, one per line, UTF-8, with no newline inside a message;
  - the server must not write anything to stdout that is not an MCP message (its logs go to stderr);
  - shutdown: close the server's stdin, wait, then terminate.
The handshake here is the one of 2025-11-25 (initialize, then notifications/initialized). The 2026-07-28 spec drops the
handshake and puts the protocol version into every request; servers written for the old one are still common.
"""
import json
import queue
import subprocess
import threading

PROTOCOL = "2025-11-25"
TIMEOUT = 15      # seconds to wait for one answer


class McpError(Exception):
    """The server could not be reached, or answered with a protocol error."""


class McpClient:
    def __init__(self, name, command, env=None):
        self.name, self.command, self.env = name, command, env
        self.proc, self.tools, self.next_id = None, [], 0
        self.lines = queue.Queue()
        self.stderr = []

    # ---- the wire
    def start(self):
        self.proc = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, encoding="utf-8", env=self.env)
        threading.Thread(target=self.pump, args=(self.proc.stdout, self.lines.put), daemon=True).start()
        threading.Thread(target=self.pump, args=(self.proc.stderr, self.stderr.append), daemon=True).start()
        info = self.request("initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                                           "clientInfo": {"name": "agent-from-scratch", "version": "11"}})
        self.server = info.get("serverInfo", {})
        self.notify("notifications/initialized")
        self.tools = self.list_tools()
        return self

    @staticmethod
    def pump(stream, sink):
        for line in stream:
            sink(line)
        sink(None)                    # the stream ended

    def send(self, message):
        self.proc.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")   # json.dumps never puts a raw newline inside
        self.proc.stdin.flush()

    def notify(self, method, params=None):
        self.send({"jsonrpc": "2.0", "method": method, **({"params": params} if params else {})})

    def request(self, method, params=None):
        self.next_id += 1
        want = self.next_id
        self.send({"jsonrpc": "2.0", "id": want, "method": method, **({"params": params} if params is not None else {})})
        while True:
            try:
                line = self.lines.get(timeout=TIMEOUT)
            except queue.Empty:
                raise McpError("%s: no answer to %s after %d s" % (self.name, method, TIMEOUT))
            if line is None:
                raise McpError("%s: the server stopped (%s)" % (self.name, "".join(self.stderr)[-200:].strip() or "no message"))
            try:
                msg = json.loads(line)
            except ValueError:
                raise McpError("%s: the server wrote something that is not JSON on stdout: %r" % (self.name, line[:80]))
            if msg.get("id") != want:         # a notification or an old answer: not ours
                continue
            if "error" in msg:
                raise McpError("%s: %s (code %s)" % (self.name, msg["error"].get("message"), msg["error"].get("code")))
            return msg.get("result", {})

    # ---- the three calls that matter
    def list_tools(self):
        tools, cursor = [], None
        while True:
            page = self.request("tools/list", {"cursor": cursor} if cursor else {})
            tools += page.get("tools", [])
            cursor = page.get("nextCursor")
            if not cursor:
                return tools

    def call(self, tool, arguments):
        """(text, is_error). A tool that failed is a result the model can read (isError); a protocol error is an exception."""
        result = self.request("tools/call", {"name": tool, "arguments": arguments or {}})
        text = "\n".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
        return text, bool(result.get("isError"))

    def close(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.close()
                self.proc.wait(timeout=3)
            except Exception:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=3)
                except Exception:
                    self.proc.kill()
