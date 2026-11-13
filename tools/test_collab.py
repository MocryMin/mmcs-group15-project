"""Behavioural regression checks; every Git integration test uses a temporary repo."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collab as c


def registered(agent="alice-ai", member="alice"):
    return dict(id=agent + "-registration", at="2026-11-03T12:00:00Z", event="register",
                agent=agent, member=member, nickname=member, model="unknown", model_version="unknown",
                harness="test", harness_version="unknown", active=True, tiers=list(c.TIERS), notes="")


def base_tree():
    events = [registered(), registered("bob-ai", "bob"), registered(c.MAINTAINER, "mocry")]
    return {c.REGISTRY: ("# Protocol\n" + "".join(c.REG_PREFIX + c.dumps(e) + "\n" for e in events)).encode(),
            "Tier1/workspaces/alice/model.py": b"old\n",
            "Tier1/workspaces/bob/model.py": b"bob\n",
            "Tier1/public/result.md": b"original result\n"}


def publication(before, path="Tier1/public/result.md", acting="Tier1", data=b"new result\n"):
    after = copy.deepcopy(before)
    tier = path.split("/")[0]
    event_id = "a" * 32
    old = before.get(path)
    archive = f"{tier}/public/archive/{event_id}/result.md" if old is not None else None
    row = dict(id=event_id, at="2026-11-03T12:00:00Z", agent="alice-ai", member="alice",
               acting_tier=acting, action="update" if old is not None else "add", path=path,
               summary="test", base_commit="parent", old_sha256=c.sha(old) if old is not None else None,
               new_sha256=c.sha(data), archive=archive, restore="Publish archived bytes" if archive else None)
    after[path] = data
    if archive:
        after[archive] = old
    log = f"{tier}/public/logs/alice-ai.jsonl"
    after[log] = before.get(log, b"") + (c.dumps(row) + "\n").encode()
    return after, row, log


def add_message(before, recipients=None):
    after = copy.deepcopy(before)
    meta = dict(id="b" * 32, at="2026-11-03T12:00:00Z", agent="alice-ai", member="alice",
                acting_tier="Tier1", recipients=recipients or ["bob-ai"], broadcast=False,
                kind="request", priority="action", reply_to=None, due_at=None)
    path = f"Tier2/agent_message/messages/20261103T120000Z_alice-ai_{meta['id']}.md"
    data = ("<!-- MESSAGE " + c.dumps(meta) + " -->\n\nPlease review this result.\n").encode()
    after[path] = data
    log = "Tier2/agent_message/logs/alice-ai.jsonl"
    after[log] = (c.dumps(dict(meta, path=path, sha256=c.sha(data))) + "\n").encode()
    return after, path, log


class ProtocolChecks(unittest.TestCase):
    def setUp(self):
        self.before = base_tree()

    def check(self, after, tier="Tier1", before=None):
        c.validate_change(self.before if before is None else before, after, "alice-ai", tier)

    def test_own_workspace_add_update_delete(self):
        for action in ("add", "update", "delete"):
            with self.subTest(action=action):
                after = copy.deepcopy(self.before)
                if action == "delete":
                    del after["Tier1/workspaces/alice/model.py"]
                else:
                    after[f"Tier1/workspaces/alice/{'new.py' if action == 'add' else 'model.py'}"] = b"new\n"
                self.check(after)

    def test_other_workspace_rejected(self):
        after = copy.deepcopy(self.before)
        after["Tier1/workspaces/bob/model.py"] = b"changed\n"
        with self.assertRaisesRegex(c.ProtocolError, "another member"):
            self.check(after)

    def test_workspace_experiment_logs_add_update_delete(self):
        path = "Tier1/workspaces/alice/experiment/logs/train.log"
        for action in ("add", "update", "delete"):
            with self.subTest(action=action):
                before = copy.deepcopy(self.before)
                if action != "add":
                    before[path] = b"epoch 1\n"
                after = copy.deepcopy(before)
                if action == "delete":
                    del after[path]
                else:
                    after[path] = b"recomputed training log\n"
                self.check(after, before=before)

    def test_other_member_experiment_log_rejected(self):
        after = copy.deepcopy(self.before)
        after["Tier1/workspaces/bob/experiment/logs/train.log"] = b"new\n"
        with self.assertRaisesRegex(c.ProtocolError, "another member"):
            self.check(after)

    def test_shared_log_namespace_remains_reserved(self):
        for area in ("public", "agent_message"):
            with self.subTest(area=area):
                after = copy.deepcopy(self.before)
                after[f"Tier1/{area}/logs/train.log"] = b"new\n"
                with self.assertRaisesRegex(c.ProtocolError, "Cannot write this log"):
                    self.check(after)

    def test_published_research_log_uses_public_operation_rules(self):
        after, _, _ = publication(self.before, path="Tier1/public/experiment/logs/train.log")
        self.check(after)

    def test_cross_tier_workspace_rejected(self):
        after = copy.deepcopy(self.before)
        after["Tier2/workspaces/alice/model.py"] = b"new\n"
        with self.assertRaisesRegex(c.ProtocolError, "acting tier"):
            self.check(after)

    def test_public_replacement_with_archive(self):
        after, _, _ = publication(self.before)
        self.check(after)

    def test_public_update_without_record_rejected(self):
        after = copy.deepcopy(self.before)
        after["Tier1/public/result.md"] = b"silent change\n"
        with self.assertRaisesRegex(c.ProtocolError, "Missing public"):
            self.check(after)

    def test_stale_archive_rejected(self):
        after, row, _ = publication(self.before)
        after[row["archive"]] = b"different old result\n"
        with self.assertRaisesRegex(c.ProtocolError, "exact parent"):
            self.check(after)

    def test_public_deletion_rejected(self):
        after = copy.deepcopy(self.before)
        del after["Tier1/public/result.md"]
        with self.assertRaisesRegex(c.ProtocolError, "cannot be deleted"):
            self.check(after)

    def test_cross_tier_add_allowed_update_rejected(self):
        after, _, _ = publication(self.before, path="Tier2/public/import.md")
        self.check(after)
        before = copy.deepcopy(self.before)
        before["Tier2/public/import.md"] = b"existing\n"
        after, _, _ = publication(before, path="Tier2/public/import.md")
        with self.assertRaisesRegex(c.ProtocolError, "Cross-tier updates"):
            self.check(after, before=before)

    def test_message_and_log_match(self):
        after, _, _ = add_message(self.before)
        self.check(after)

    def test_unknown_recipient_rejected(self):
        after, _, _ = add_message(self.before, ["not-registered"])
        with self.assertRaisesRegex(c.ProtocolError, "recipient"):
            self.check(after)

    def test_message_hash_detects_edit(self):
        after, path, _ = add_message(self.before)
        after[path] += b"unlogged\n"
        with self.assertRaisesRegex(c.ProtocolError, "hash"):
            self.check(after)

    def test_old_message_immutable(self):
        before, path, _ = add_message(self.before)
        after = copy.deepcopy(before)
        after[path] += b"edit\n"
        with self.assertRaisesRegex(c.ProtocolError, "immutable"):
            self.check(after, before=before)

    def test_old_log_cannot_change(self):
        before, _, log = publication(self.before)
        after = copy.deepcopy(before)
        after[log] = after[log].replace(b'"test"', b'"rewritten"')
        with self.assertRaisesRegex(c.ProtocolError, "append-only"):
            self.check(after, before=before)

    def test_old_archive_immutable(self):
        before, row, _ = publication(self.before)
        after = copy.deepcopy(before)
        after[row["archive"]] = b"changed\n"
        with self.assertRaisesRegex(c.ProtocolError, "immutable"):
            self.check(after, before=before)

    def test_registration_preserves_old_events(self):
        before = self.before
        after = copy.deepcopy(before)
        event = registered("charlie-ai", "charlie")
        after[c.REGISTRY] += (c.REG_PREFIX + c.dumps(event) + "\n").encode()
        for tier in c.TIERS:
            after[f"{tier}/workspaces/charlie/WORKSPACE.md"] = b"hello\n"
        c.validate_change(before, after, "charlie-ai", "registration")
        after[c.REGISTRY] = after[c.REGISTRY].replace(b'"nickname":"alice"', b'"nickname":"changed"')
        with self.assertRaisesRegex(c.ProtocolError, "Past registrations"):
            c.validate_change(before, after, "charlie-ai", "registration")

    def test_path_traversal_rejected(self):
        for path in ("../escape", "/absolute", "C:/absolute", "a/../../b", "a\\b", "a/.git/config"):
            with self.subTest(path=path), self.assertRaises(c.ProtocolError):
                c.safe_path(path)

    def test_root_changes_require_control(self):
        after = copy.deepcopy(self.before)
        after["tools/other.py"] = b"code\n"
        with self.assertRaisesRegex(c.ProtocolError, "control"):
            self.check(after)


class ConcurrentGitChecks(unittest.TestCase):
    def test_tree_batches_duplicate_and_binary_blobs(self):
        with tempfile.TemporaryDirectory(prefix="mmcs-tree-test-") as tmp:
            repo = Path(tmp)
            c.git("init", str(repo))
            data = {"raw.bin": b"\x00\n\r\n\xff", "duplicate.bin": b"\x00\n\r\n\xff",
                    "empty.bin": b"", "space in name.bin": b"without final newline"}
            for name, content in data.items():
                (repo / name).write_bytes(content)
            c.git("add", ".", cwd=repo)
            ref = c.git_text("write-tree", cwd=repo)
            with patch.object(c, "git", wraps=c.git) as git:
                self.assertEqual(c.tree(ref, repo), data)
            self.assertEqual([call.args[0] for call in git.call_args_list], ["ls-tree", "cat-file"])
            self.assertEqual(len(git.call_args_list[-1].kwargs["data"].splitlines()), 3)

    @unittest.skipUnless(sys.platform == "win32", "Windows console behavior")
    def test_background_child_has_no_console(self):
        result = c.run_child([sys.executable, "-c",
                              "import ctypes; print(ctypes.windll.kernel32.GetConsoleWindow())"],
                             capture_output=True, check=True)
        self.assertEqual(result.stdout.strip(), b"0")

    def test_cli_registration_public_update_restore_and_message(self):
        with tempfile.TemporaryDirectory(prefix="mmcs-helper-test-") as tmp:
            repo = Path(tmp)
            c.git("init", "--initial-branch=main", str(repo))
            c.git("config", "user.name", "Test", cwd=repo)
            c.git("config", "user.email", "test@example.invalid", cwd=repo)
            for path, data in base_tree().items():
                target = repo / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            (repo / ".gitattributes").write_text("* text=auto eol=lf\n", encoding="utf-8")
            c.git("add", ".", cwd=repo)
            c.git("commit", "-m", "Bootstrap", cwd=repo)
            initial = c.git_text("rev-parse", "HEAD", cwd=repo)
            helper = str(Path(c.__file__).resolve())

            def cli(*args, success=True):
                result = c.run_child([sys.executable, helper, *args], cwd=repo, capture_output=True)
                if success:
                    self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
                else:
                    self.assertNotEqual(result.returncode, 0)
                return result

            def commit(tier):
                c.git("add", ".", cwd=repo)
                cli("commit", "--tier", tier, "--message", "Test operation")

            cli("setup", "--agent", "charlie-ai")
            cli("register", "--agent", "charlie-ai", "--member", "charlie", "--nickname", "Charlie",
                "--model", "unknown", "--harness", "test")
            commit("registration")
            source = repo / "Tier1/workspaces/charlie/source.md"
            source.write_bytes(b"first version\r\n")
            publish_args = ("publish", "--tier", "Tier1", "--area", "Tier1", "--path", "result.md",
                            "--source", str(source), "--summary", "test publication")
            cli(*publish_args)
            # A second edit before the first is committed cannot generate a misleading preimage.
            cli(*publish_args, success=False)
            cli("message", "--tier", "Tier1", "--area", "Tier2", "--to", "bob-ai",
                "--body-file", str(source), "--kind", "request")
            commit("Tier1")
            source.write_text("second version\n", encoding="utf-8")
            cli(*publish_args)
            commit("Tier1")
            rows = c.log_rows((repo / "Tier1/public/logs/charlie-ai.jsonl").read_bytes())
            archive = repo / rows[-1]["archive"]
            self.assertEqual(archive.read_bytes(), b"first version\n")
            cli("publish", "--tier", "Tier1", "--area", "Tier1", "--path", "result.md",
                "--source", str(archive), "--summary", "Restore previous version")
            commit("Tier1")
            self.assertEqual((repo / "Tier1/public/result.md").read_bytes(), b"first version\n")
            self.assertEqual(c.validate_range(initial, "HEAD", repo), 4)

    def test_two_clones_preserve_both_writers(self):
        with tempfile.TemporaryDirectory(prefix="mmcs-collab-test-") as tmp:
            folder = Path(tmp)
            remote, a, b = [folder / name for name in ("remote.git", "a", "b")]
            c.git("init", "--bare", "--initial-branch=main", str(remote))
            c.git("clone", str(remote), str(a))
            for key, value in (("user.name", "Test"), ("user.email", "test@example.invalid")):
                c.git("config", key, value, cwd=a)
            for path, data in base_tree().items():
                target = a / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            c.git("add", ".", cwd=a)
            c.git("commit", "-m", "Bootstrap", cwd=a)
            c.git("push", "origin", "main", cwd=a)
            c.git("clone", str(remote), str(b))
            for key, value in (("user.name", "Test"), ("user.email", "test@example.invalid")):
                c.git("config", key, value, cwd=b)
            for repo, member, agent in ((a, "alice", "alice-ai"), (b, "bob", "bob-ai")):
                target = repo / f"Tier1/workspaces/{member}/result.txt"
                target.write_text(member, encoding="utf-8")
                c.git("add", str(target), cwd=repo)
                c.git("commit", "-m", f"Share {member}", "-m", f"Agent-ID: {agent}\nActing-Tier: Tier1", cwd=repo)
            c.validate_range("origin/main", "HEAD", a)
            c.git("push", "origin", "main", cwd=a)
            rejected = c.git("push", "origin", "main", cwd=b, check=False)
            self.assertNotEqual(rejected.returncode, 0)
            c.git("fetch", "origin", cwd=b)
            with self.assertRaisesRegex(c.ProtocolError, "Remote advanced"):
                c.validate_range("origin/main", "HEAD", b)
            c.git("rebase", "origin/main", cwd=b)
            self.assertEqual(c.validate_range("origin/main", "HEAD", b), 1)
            c.git("push", "origin", "main", cwd=b)
            self.assertEqual((b / "Tier1/workspaces/alice/result.txt").read_text(), "alice")
            self.assertEqual((b / "Tier1/workspaces/bob/result.txt").read_text(), "bob")


if __name__ == "__main__":
    unittest.main()
