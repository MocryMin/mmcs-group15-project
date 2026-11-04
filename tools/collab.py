#!/usr/bin/env python3
"""Small, standard-library-only collaboration helper. Local cooperative checks."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

TIERS = ("Tier1", "Tier2")
MAINTAINER = "mocry-codex"
REGISTRY = "agent_protocol.md"
REG_PREFIX = "REGISTRATION "
ID_PATTERN = re.compile(r"[a-z][a-z0-9-]{0,47}\Z")
KINDS = ("notice", "request", "reply", "ack", "decision", "status", "correction")


class ProtocolError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ProtocolError(message)


def run_child(args, **kwargs):
    """Keep background commands from allocating a console on Windows."""
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.run(args, **kwargs)


def git(*args, cwd=None, check=True, data=None):
    result = run_child(["git", *args], cwd=cwd, input=data, capture_output=True)
    if check and result.returncode:
        raise ProtocolError(result.stderr.decode("utf-8", "replace").strip())
    return result


def git_text(*args, cwd=None):
    return git(*args, cwd=cwd).stdout.decode("utf-8").strip()


def root():
    return Path(git_text("rev-parse", "--show-toplevel"))


def dumps(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def clean_bytes(repo, path, data):
    """Use the representation Git will commit, including text line endings."""
    blob = git("hash-object", "-w", f"--path={path}", "--stdin", cwd=repo, data=data).stdout.strip().decode()
    return git("cat-file", "blob", blob, cwd=repo).stdout


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def valid_id(value):
    require(bool(ID_PATTERN.fullmatch(value)), f"Invalid ID: {value}")
    return value


def safe_path(value):
    p = PurePosixPath(value)
    require(value and "\\" not in value and not p.is_absolute(), "Use a relative POSIX path")
    require(all(part not in (".", "..", "") for part in value.split("/")), "Unsafe path")
    require(not any(":" in part or part.lower() == ".git" for part in p.parts), "Unsafe path")
    return p


def destination(repo, relative):
    safe_path(relative)
    p = repo / relative
    require(not any(parent.is_symlink() for parent in [p, *p.parents] if parent != repo.parent),
            "Symlink destinations are not supported")
    require(p.resolve().is_relative_to(repo.resolve()), "Path leaves repository")
    return p


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def append_line(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_bytes() if path.exists() else b""
    require(not old or old.endswith(b"\n"), f"Missing final newline: {path}")
    with path.open("ab") as stream:
        stream.write((dumps(value) + "\n").encode("utf-8"))


def registration_events(data):
    return [json.loads(line[len(REG_PREFIX):]) for line in data.decode("utf-8").splitlines()
            if line.startswith(REG_PREFIX)]


def registry(data):
    result, seen = {}, set()
    for event in registration_events(data):
        for field in ("id", "at", "event", "agent", "member", "nickname", "model",
                      "model_version", "harness", "harness_version", "active", "tiers", "notes"):
            require(field in event, f"Registration missing {field}")
        valid_id(event["agent"])
        valid_id(event["member"])
        require(event["id"] not in seen, "Duplicate registration event")
        seen.add(event["id"])
        previous = result.get(event["agent"])
        require(event["event"] == ("update" if previous else "register"), "Invalid registration sequence")
        if previous:
            require(previous["member"] == event["member"], "Agent member cannot change")
        result[event["agent"]] = event
    return result


def identity(repo):
    agent = git_text("config", "--get", "collab.agent", cwd=repo)
    entries = registry((repo / REGISTRY).read_bytes())
    require(agent in entries and entries[agent]["active"], "Register your active agent first")
    return entries[agent]


def tree(ref, cwd=None):
    """Read committed or staged trees without checking them out."""
    paths = {}
    for entry in git("ls-tree", "-rz", ref, cwd=cwd).stdout.split(b"\0"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
        mode, kind, blob = metadata.split()
        require(mode in (b"100644", b"100755") and kind == b"blob", "Symlinks/submodules are not allowed")
        paths[path.decode("utf-8")] = blob
    if not paths:
        return {}

    blobs = dict.fromkeys(paths.values())
    request = b"\n".join(blobs) + b"\n"
    with io.BytesIO(git("cat-file", "--batch", cwd=cwd, data=request).stdout) as response:
        for blob in blobs:
            header = response.readline().split()
            require(len(header) == 3 and header[:2] == [blob, b"blob"] and header[2].isdigit(),
                    f"Unexpected Git blob response: {blob.decode()}")
            size = int(header[2])
            data = response.read(size)
            require(len(data) == size and response.read(1) == b"\n", "Truncated Git blob response")
            blobs[blob] = data
        require(not response.read(1), "Unexpected trailing Git blob data")
    return {path: blobs[blob] for path, blob in paths.items()}


def log_rows(data):
    require(not data or data.endswith(b"\n"), "Logs must end with a newline")
    return [json.loads(line) for line in data.decode("utf-8").splitlines()]


def validate_change(before, after, agent, acting_tier):
    """Validate one complete commit, including its matching log/archive events."""
    require(acting_tier in (*TIERS, "registration", "control"), "Invalid acting tier")
    require(REGISTRY in after, "Missing registry")
    old_registry = before.get(REGISTRY, b"")
    old_events = registration_events(old_registry)
    new_events = registration_events(after[REGISTRY])
    require(new_events[:len(old_events)] == old_events, "Past registrations cannot change")
    entries = registry(after[REGISTRY])
    require(agent in entries and entries[agent]["active"], "Unregistered/inactive actor")
    member = entries[agent]["member"]
    control = acting_tier == "control" and agent == MAINTAINER
    require(acting_tier != "control" or control, "Only maintainer may change infrastructure")
    added_events = new_events[len(old_events):]
    require(all(e["agent"] == agent for e in added_events), "Cannot register/update another agent")
    if added_events:
        require(acting_tier == "registration", "Use a registration commit")
    if not control:
        require(after[REGISTRY].startswith(old_registry), "Global protocol is append-only for members")
        suffix = after[REGISTRY][len(old_registry):].decode("utf-8")
        require(all(not line or line.startswith(REG_PREFIX) for line in suffix.splitlines()),
                "Only registration lines may be appended")

    changes = {p for p in before.keys() | after.keys() if before.get(p) != after.get(p)}
    new_log_events = {}
    all_ids, all_messages = set(), {}
    for p, data in after.items():
        if re.fullmatch(r"Tier[12]/(?:public|agent_message)/logs/[a-z0-9-]+\.jsonl", p):
            for record in log_rows(data):
                require(record["id"] not in all_ids, "Duplicate log event ID")
                all_ids.add(record["id"])
                if "/agent_message/" in p:
                    all_messages[record["id"]] = record
    for p in sorted(changes):
        safe_path(p)
        if "/logs/" not in p or not p.startswith(TIERS):
            continue
        parts = p.split("/")
        require(len(parts) == 4 and parts[1] in ("public", "agent_message")
                and parts[3] == f"{agent}.jsonl", f"Cannot write this log: {p}")
        require(p in after and after[p].startswith(before.get(p, b"")), f"Log is append-only: {p}")
        appended = after[p][len(before.get(p, b"")):]
        require(bool(appended), "Empty log change")
        records = log_rows(appended)
        for record in records:
            require(record["agent"] == agent and record["member"] == member
                    and record["acting_tier"] == acting_tier, "Log actor differs from commit")
            require(record["at"].endswith("Z"), "Use UTC event timestamps")
            datetime.fromisoformat(record["at"].replace("Z", "+00:00"))
            target = record["path"]
            safe_path(target)
            require(target.startswith(f"{parts[0]}/"), "Log is in the wrong tier")
            require(target not in new_log_events, "One operation per path per commit")
            new_log_events[target] = (parts[1], record)

    consumed, expected_archives = set(), set()
    for p in sorted(changes):
        parts = p.split("/")
        if p == REGISTRY:
            continue
        if parts[0] not in TIERS:
            require(control, f"Root/infrastructure edit requires maintainer control commit: {p}")
            continue
        tier = parts[0]
        require(len(parts) >= 3, f"Unexpected tier path: {p}")
        area = parts[1]
        if area == "workspaces":
            if len(parts) == 3 and parts[2] == "README.md":
                require(control, "Workspace guide is infrastructure")
                continue
            require(parts[2] == member, f"Cannot modify another member's workspace: {p}")
            if acting_tier == "registration":
                require(p not in before and p in after, "Registration only adds workspace files")
            else:
                require(acting_tier == tier, "Workspace edits must match acting tier")
            continue
        require(acting_tier != "registration", "Registration commit contains shared artifacts")
        require(area in ("public", "agent_message"), f"Unknown area: {p}")
        require(p in after, f"Shared files cannot be deleted: {p}")
        if parts[2] == "logs":
            continue
        if area == "public" and parts[2] == "archive":
            require(p not in before, f"Archives are immutable: {p}")
            continue
        if area == "agent_message" and parts[2] == "messages":
            require(p not in before, f"Messages are immutable: {p}")
            require(p in new_log_events and new_log_events[p][0] == "agent_message", "Missing message log")
            r = new_log_events[p][1]
            first = after[p].split(b"\n", 1)[0].decode("utf-8")
            require(first.startswith("<!-- MESSAGE ") and first.endswith(" -->"), "Missing message metadata")
            metadata = json.loads(first[len("<!-- MESSAGE "):-len(" -->")])
            require(metadata == {k: v for k, v in r.items() if k not in ("path", "sha256")},
                    "Message header and log differ")
            require(sha(after[p]) == r["sha256"], "Message content hash differs")
            require(r["id"] in parts[-1] and f"_{agent}_" in parts[-1], "Message filename does not identify sender/ID")
            recipients = r["recipients"]
            require(bool(recipients) != bool(r["broadcast"]), "Choose recipients OR broadcast")
            require(all(x in entries and entries[x]["active"] for x in recipients), "Unknown/inactive recipient")
            require(r["kind"] in KINDS and r["priority"] in ("info", "action", "blocker"), "Invalid message type")
            if r["reply_to"]:
                require(r["reply_to"] in all_messages and r["reply_to"] != r["id"], "Unknown/self reply target")
            consumed.add(p)
            continue
        if area == "agent_message":
            require(control and parts[2] in ("README.md", "agent_skill_protocol.md"), "Unknown message-area file")
        if parts[2] in ("README.md", "agent_skill_protocol.md"):
            require(control, "Zone guidance requires maintainer control commit")
        require(p in new_log_events and new_log_events[p][0] == "public", f"Missing public operation log: {p}")
        r = new_log_events[p][1]
        require(sha(after[p]) == r["new_sha256"], f"New public hash differs: {p}")
        if p in before:
            require(acting_tier == tier or control, "Cross-tier updates are forbidden; add or request instead")
            archive = r["archive"]
            require(r["action"] == "update" and r["old_sha256"] == sha(before[p]), "Old public hash differs")
            require(isinstance(archive, str) and archive.startswith(f"{tier}/public/archive/{r['id']}/"), "Invalid archive path")
            require(archive not in before and after.get(archive) == before[p], "Archive must preserve exact parent bytes")
            require(bool(r.get("restore")), "Missing restore instructions")
            expected_archives.add(archive)
        else:
            require(r["action"] == "add" and r["old_sha256"] is None and r["archive"] is None,
                    "New file must have an add record")
        consumed.add(p)
    require(consumed == set(new_log_events), "Log contains operations without matching file changes")
    archives = {p for p in changes if re.match(r"Tier[12]/public/archive/", p)}
    require(archives == expected_archives, "Unlogged/orphan archive")


def validate_range(base, head, cwd=None):
    if base:
        require(git("merge-base", "--is-ancestor", base, head, cwd=cwd, check=False).returncode == 0,
                "Remote advanced or history would be replaced. Fetch and reconcile first.")
    commits = git_text("rev-list", "--reverse", f"{base}..{head}" if base else head, cwd=cwd).splitlines()
    for commit in commits:
        parents = git_text("rev-list", "--parents", "-n", "1", commit, cwd=cwd).split()[1:]
        if not parents:
            require(base is None, "Unexpected root commit")
            continue  # Initial repository bootstrap is explicitly trusted.
        require(len(parents) == 1, "Rebase unpublished work; merge commits are not accepted")
        body = git_text("show", "-s", "--format=%B", commit, cwd=cwd)
        actors = re.findall(r"^Agent-ID: (.+)$", body, re.M)
        tiers = re.findall(r"^Acting-Tier: (.+)$", body, re.M)
        require(len(actors) == len(tiers) == 1, f"Missing/ambiguous trailers: {commit[:8]}")
        validate_change(tree(parents[0], cwd), tree(commit, cwd), actors[0], tiers[0])
    return len(commits)


def setup(args, repo):
    valid_id(args.agent)
    git("config", "collab.agent", args.agent, cwd=repo)
    git("config", "collab.python", Path(sys.executable).resolve().as_posix(), cwd=repo)
    git("config", "core.hooksPath", ".githooks", cwd=repo)
    print(f"Configured {args.agent}; installed local pre-push check. Git author unchanged.")


def register(args, repo):
    valid_id(args.member)
    valid_id(args.agent)
    p = repo / REGISTRY
    existing = registry(p.read_bytes())
    require((args.agent in existing) == args.update, "Use --update only for an existing agent")
    if args.update:
        require(existing[args.agent]["member"] == args.member, "Cannot change agent member")
    event = dict(id=uuid.uuid4().hex, at=now(), event="update" if args.update else "register",
                 agent=args.agent, member=args.member, nickname=args.nickname, model=args.model,
                 model_version=args.model_version, harness=args.harness, harness_version=args.harness_version,
                 active=True, tiers=list(TIERS), notes=args.notes)
    require(p.read_bytes().endswith(b"\n"), "Registry must end with newline")
    with p.open("ab") as stream:
        stream.write((REG_PREFIX + dumps(event) + "\n").encode("utf-8"))
    for tier in TIERS:
        workspace = destination(repo, f"{tier}/workspaces/{args.member}")
        workspace.mkdir(parents=True, exist_ok=True)
        for name, data in {
            "WORKSPACE.md": f"# {args.nickname} — {tier}\n\nMember ID: `{args.member}`.\n\nKeep drafts, tasks, findings and resumable state here. Other members may read; only this member's agents may write. Publish shared results through the public helper.\n",
            "coordination_state.json": json.dumps({"member": args.member, "seen_message_ids": [], "tasks": [], "handoff": ""}, indent=2) + "\n",
        }.items():
            if not (workspace / name).exists():
                write_new(workspace / name, data.encode("utf-8"))
    print(f"Appended {event['event']} event {event['id']}; created missing workspaces in both tiers.")


def publish(args, repo):
    who = identity(repo)
    relative = safe_path(args.path)
    require(relative.parts[0] not in ("archive", "logs"), "Reserved public path")
    if relative.parts[0] in ("README.md", "agent_skill_protocol.md"):
        require(who["agent"] == MAINTAINER and args.tier == "control", "Maintainer control operation required")
    path = f"{args.area}/public/{relative}"
    target = destination(repo, path)
    old = clean_bytes(repo, path, target.read_bytes()) if target.exists() else None
    committed = git("show", f"HEAD:{path}", cwd=repo, check=False)
    expected = committed.stdout if committed.returncode == 0 else None
    require(old == expected, "Target has unpublished edits; publish once per path per commit from a workspace source")
    require(old is None or args.tier in (args.area, "control"), "Cross-tier updates are forbidden")
    require(args.tier != "control" or who["agent"] == MAINTAINER, "Maintainer required")
    data = Path(args.source).read_bytes()
    data = clean_bytes(repo, path, data)
    require(old != data, "No content change to publish")
    event_id = uuid.uuid4().hex
    archive = f"{args.area}/public/archive/{event_id}/{relative}" if old is not None else None
    record = dict(id=event_id, at=now(), agent=who["agent"], member=who["member"], acting_tier=args.tier,
                  action="update" if old is not None else "add", path=path, summary=args.summary,
                  base_commit=git_text("rev-parse", "HEAD", cwd=repo),
                  old_sha256=sha(old) if old is not None else None, new_sha256=sha(data), archive=archive,
                  restore=f"Publish {archive} as source for {path}; retain history." if archive else None)
    if archive:
        write_new(destination(repo, archive), old)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    append_line(destination(repo, f"{args.area}/public/logs/{who['agent']}.jsonl"), record)
    print(dumps(record))


def message(args, repo):
    who = identity(repo)
    entries = registry((repo / REGISTRY).read_bytes())
    require(bool(args.to) != bool(args.broadcast), "Choose --to OR --broadcast")
    require(all(x in entries and entries[x]["active"] for x in (args.to or [])), "Unknown/inactive recipient")
    if args.reply_to:
        known = {r["id"] for tier in TIERS for p in (repo / tier / "agent_message" / "logs").glob("*.jsonl")
                 for r in log_rows(p.read_bytes())}
        require(args.reply_to in known, "Unknown reply-to ID")
    if args.due_at:
        require(datetime.fromisoformat(args.due_at.replace("Z", "+00:00")).tzinfo is not None, "Deadline needs timezone")
    meta = dict(id=uuid.uuid4().hex, at=now(), agent=who["agent"], member=who["member"],
                acting_tier=args.tier, recipients=sorted(set(args.to or [])), broadcast=args.broadcast,
                kind=args.kind, priority=args.priority, reply_to=args.reply_to, due_at=args.due_at)
    stamp = meta["at"].replace("-", "").replace(":", "").replace(".", "")
    path = f"{args.area}/agent_message/messages/{stamp}_{who['agent']}_{meta['id']}.md"
    body = Path(args.body_file).read_text(encoding="utf-8-sig")
    data = ("<!-- MESSAGE " + dumps(meta) + " -->\n\n" + body.rstrip() + "\n").encode("utf-8")
    write_new(destination(repo, path), data)
    append_line(destination(repo, f"{args.area}/agent_message/logs/{who['agent']}.jsonl"),
                dict(meta, path=path, sha256=sha(data)))
    print(path)


def commit(args, repo):
    agent = git_text("config", "--get", "collab.agent", cwd=repo)
    staged = git_text("write-tree", cwd=repo)
    validate_change(tree("HEAD", repo), tree(staged, repo), agent, args.tier)
    result = git("commit", "-m", args.message, "-m", f"Agent-ID: {agent}\nActing-Tier: {args.tier}", cwd=repo)
    print(result.stdout.decode("utf-8", "replace"))


def push(args, repo):
    require(git_text("branch", "--show-current", cwd=repo) == "main", "Integrate on local main before publishing")
    require(not git_text("status", "--porcelain", cwd=repo), "Commit or safely set aside local changes before push")
    git("fetch", "origin", "main", cwd=repo)
    count = validate_range("origin/main", "HEAD", repo)
    result = git("push", "origin", "HEAD:main", cwd=repo)
    print(result.stdout.decode("utf-8", "replace") + result.stderr.decode("utf-8", "replace"))
    print(f"Checked {count} unpublished commit(s).")


def pre_push(args, repo):
    for line in sys.stdin:
        local_ref, local_sha, remote_ref, remote_sha = line.split()
        require(remote_ref == "refs/heads/main", "This shared remote uses main only")
        require(set(local_sha) != {"0"}, "Branch deletion is forbidden")
        validate_range(None if set(remote_sha) == {"0"} else remote_sha, local_sha, repo)
    print("Collaboration pre-push check passed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("setup")
    p.add_argument("--agent", required=True)
    p = sub.add_parser("register")
    for key in ("member", "agent", "nickname", "model", "harness"):
        p.add_argument("--" + key, required=True)
    p.add_argument("--model-version", default="unknown")
    p.add_argument("--harness-version", default="unknown")
    p.add_argument("--notes", default="")
    p.add_argument("--update", action="store_true")
    p = sub.add_parser("publish")
    p.add_argument("--tier", choices=(*TIERS, "control"), required=True)
    p.add_argument("--area", choices=TIERS, required=True)
    for key in ("path", "source", "summary"):
        p.add_argument("--" + key, required=True)
    p = sub.add_parser("message")
    p.add_argument("--tier", choices=TIERS, required=True)
    p.add_argument("--area", choices=TIERS, required=True)
    p.add_argument("--to", action="append")
    p.add_argument("--broadcast", action="store_true")
    p.add_argument("--body-file", required=True)
    p.add_argument("--kind", choices=KINDS, default="notice")
    p.add_argument("--priority", choices=("info", "action", "blocker"), default="info")
    p.add_argument("--reply-to")
    p.add_argument("--due-at")
    p = sub.add_parser("commit")
    p.add_argument("--tier", choices=(*TIERS, "registration", "control"), required=True)
    p.add_argument("--message", required=True)
    p = sub.add_parser("validate")
    p.add_argument("--base", default="origin/main")
    p.add_argument("--head", default="HEAD")
    sub.add_parser("push")
    sub.add_parser("pre-push")
    args = parser.parse_args()
    repo = root()
    if args.command == "validate":
        print(f"Validated {validate_range(args.base, args.head, repo)} commit(s).")
    else:
        globals()[args.command.replace("-", "_")](args, repo)


if __name__ == "__main__":
    try:
        main()
    except (ProtocolError, OSError, ValueError, KeyError) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        sys.exit(1)
