"""Package source, frozen inputs, evidence and computed schedules; never include the environment."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent


def package():
    files = sorted(p for p in ROOT.rglob('*') if p.is_file()
                   and not {'.venv', '__pycache__'}.intersection(p.relative_to(ROOT).parts)
                   and p.name != 'PACKAGE_MANIFEST.json')
    manifest = {p.relative_to(ROOT).as_posix(): dict(bytes=p.stat().st_size,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files}
    mp = ROOT / 'PACKAGE_MANIFEST.json'
    mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    target = ROOT.parent / 'MMCS_Tier1_Strengthened_20261110_v5.zip'
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in files + [mp]:
            z.write(p, (Path(ROOT.name) / p.relative_to(ROOT)).as_posix())
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        assert len(z.infolist()) == len(manifest) + 1
        for relative, record in manifest.items():
            data = z.read(ROOT.name + '/' + relative)
            assert len(data) == record['bytes']
            assert hashlib.sha256(data).hexdigest() == record['sha256']
    print(json.dumps(dict(zip=str(target), bytes=target.stat().st_size,
                          files=len(manifest)+1, sha256=hashlib.sha256(target.read_bytes()).hexdigest()), indent=2))


if __name__ == '__main__':
    package()
