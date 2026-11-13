"""Cooperative atomic lock for public Playwright calls during this research run."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['acquire', 'release', 'status'])
parser.add_argument('--owner', required=True)
args = parser.parse_args()
folder = Path(__file__).resolve().parent / 'public-browser.lock'
if args.action == 'acquire':
    try:
        folder.mkdir()
    except FileExistsError:
        print('BUSY')
    else:
        (folder / 'owner.json').write_text(json.dumps({'owner': args.owner, 'at': datetime.now(timezone.utc).isoformat()}), encoding='utf-8')
        print('ACQUIRED')
elif args.action == 'release':
    data = json.loads((folder / 'owner.json').read_text(encoding='utf-8'))
    if data['owner'] != args.owner:
        raise SystemExit('NOT YOUR LOCK')
    (folder / 'owner.json').unlink()
    folder.rmdir()
    print('RELEASED')
else:
    print((folder / 'owner.json').read_text(encoding='utf-8') if folder.exists() else 'FREE')
