from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import json,os
root=Path(__file__).resolve().parent
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root/'dist')))
state={'url':f'http://127.0.0.1:{server.server_port}','pid':os.getpid()}
(root/'PREVIEW_SERVER.json').write_text(json.dumps(state),encoding='utf-8')
print(json.dumps(state),flush=True)
server.serve_forever()
