import argparse, json, os, pathlib, subprocess, sys, tempfile
parser = argparse.ArgumentParser(description="Collect public data through an isolated official Playwright MCP.")
parser.add_argument("javascript", type=pathlib.Path)
parser.add_argument("output", type=pathlib.Path)
parser.add_argument("--mcp-cli", type=pathlib.Path, required=True)
parser.add_argument("--browser-executable", type=pathlib.Path, required=True)
args = parser.parse_args()
cli, exe = args.mcp_cli, args.browser_executable
with tempfile.TemporaryDirectory(prefix="mmcs-isolated-public-browser-") as out, tempfile.TemporaryFile(mode="w+b") as err:
    p = subprocess.Popen(["node", str(cli), "--headless", "--isolated", "--executable-path", str(exe), "--output-dir", out], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    try:
        def send(message):
            p.stdin.write(json.dumps(dict(jsonrpc="2.0", **message))+"\n")
            p.stdin.flush()
        def ask(n, method, params=None):
            send(dict(id=n, method=method, params=params or {}))
            for line in p.stdout:
                try:
                    item=json.loads(line)
                except ValueError:
                    continue
                if item.get("id")==n:
                    return item
            err.seek(0)
            raise RuntimeError(err.read().decode("utf-8","replace")[-3000:])
        ask(1,"initialize",dict(protocolVersion="2025-03-26",capabilities={},clientInfo=dict(name="mmcs-public-data",version="1")))
        send(dict(method="notifications/initialized"))
        available=ask(2,"tools/list")["result"]["tools"]
        run=next((x["name"] for x in available if x["name"] in ("browser_run_code_unsafe","browser_run_code")),None)
        if not run:
            raise RuntimeError([x["name"] for x in available])
        code=args.javascript.read_text(encoding="utf-8")
        result=ask(3,"tools/call",dict(name=run,arguments=dict(code=code)))

        import gzip, re
        if "error" in result:
            raise RuntimeError(result["error"])
        content=result["result"]["content"]
        text=next(x["text"] for x in content if x["type"]=="text")
        match=re.search(r"### Result\n([\s\S]*?)\n### Ran Playwright code",text)
        if not match:
            raise RuntimeError(text[:3000])
        value=json.loads(match.group(1))
        target=args.output
        target.parent.mkdir(parents=True,exist_ok=True)
        with gzip.open(target,"wt",encoding="utf-8") as stream:
            json.dump(value,stream,ensure_ascii=False,separators=(",",":"))
        print(json.dumps(dict(saved=str(target),bytes=target.stat().st_size,keys=list(value) if isinstance(value,dict) else len(value)),ensure_ascii=True))
    finally:
        p.stdin.close()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.terminate()
            p.wait(timeout=5)
