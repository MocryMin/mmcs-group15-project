"""Loopback-only visual QA server; exposes just the standalone chart file."""
from pathlib import Path
from http.server import HTTPServer,BaseHTTPRequestHandler
import json
import os

ROOT=Path(__file__).resolve().parent


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?",1)[0] not in ("/","/MMCS-data-explorer.html"):
            self.send_error(404);return
        content=(ROOT/"MMCS-data-explorer.html").read_bytes()
        self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(content)));self.end_headers();self.wfile.write(content)


if __name__=="__main__":
    server=HTTPServer(("127.0.0.1",0),Handler)
    state={"url":f"http://127.0.0.1:{server.server_port}","pid":os.getpid()}
    (ROOT/"PREVIEW_SERVER.json").write_text(json.dumps(state),encoding="utf-8")
    print(json.dumps(state),flush=True);server.serve_forever()
