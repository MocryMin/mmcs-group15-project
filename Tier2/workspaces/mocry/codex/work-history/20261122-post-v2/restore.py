"""Verify and extract archived research to a separate experiments directory."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import zipfile


HERE = Path(__file__).resolve().parent


def sha(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def inside(root, name):
    relative = PurePosixPath(name)
    if relative.is_absolute() or any(p in {"..", "."} or ":" in p or "\\" in p for p in relative.parts):
        raise ValueError(f"Unsafe archived path: {name}")
    path = root.joinpath(*relative.parts)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Archive path leaves its destination: {name}")
    return path


def restore(target, verify_only, group_names=()):
    index = json.loads((HERE / "MANIFEST.json").read_text(encoding="utf-8"))
    requested = set(group_names)
    groups = [group for group in index["groups"] if not requested or group["name"] in requested]
    missing = requested - {group["name"] for group in groups}
    if missing:
        raise ValueError(f"Unknown ZIP group: {', '.join(sorted(missing))}")

    count = 0
    with tempfile.TemporaryDirectory(prefix="mmcs-research-") as temp:
        for group in groups:
            zipped = Path(temp) / "archive.zip"
            with zipped.open("wb") as combined:
                for part in group["parts"]:
                    source = inside(HERE, part["path"])
                    if source.stat().st_size != part["size"] or sha(source) != part["sha256"]:
                        raise ValueError(f"Archive volume differs from manifest: {part['path']}")
                    with source.open("rb") as read:
                        shutil.copyfileobj(read, combined, length=4*1024**2)
            if sha(zipped) != group["zip_sha256"]:
                raise ValueError(f"Reassembled ZIP differs: {group['name']}")
            with zipfile.ZipFile(zipped) as archive:
                if archive.namelist() != [item["path"] for item in group["files"]]:
                    raise ValueError(f"ZIP members differ: {group['name']}")
                for item in group["files"]:
                    name = item["path"]
                    destination = inside(target, name)
                    with archive.open(name) as entry:
                        if hashlib.file_digest(entry, "sha256").hexdigest() != item["sha256"]:
                            raise ValueError(f"Archive member differs: {name}")
                    if not verify_only:
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        if destination.exists():
                            if sha(destination) != item["sha256"]:
                                raise FileExistsError(f"Existing different file: {destination}")
                        else:
                            with archive.open(name) as entry, destination.open("xb") as file:
                                shutil.copyfileobj(entry, file)
                    count += 1
    print(f"Verified {count} file(s).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, nargs="?", default=HERE / "extracted")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--group", action="append", default=[], metavar="ZIP",
                        help="verify or extract a named ZIP group (repeat for multiple groups)")
    args = parser.parse_args()
    restore(args.destination, args.verify_only, args.group)
