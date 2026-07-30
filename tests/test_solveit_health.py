import importlib.util
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / "home/dot_local/bin/executable_solveit-health"


def _load():
    loader = SourceFileLoader("solveit_health", str(CLI))
    spec = importlib.util.spec_from_file_location("solveit_health", CLI, loader=loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


health = _load()


def _transcript(root, name, entries):
    proj = root / name
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "s.jsonl").write_text("\n".join(json.dumps(e) for e in entries) + "\n")


def _user(text, ts="2026-07-30T10:00:00Z"):
    return {"type": "user", "timestamp": ts, "message": {"role": "user", "content": text}}


def _assistant(*blocks):
    return {"type": "assistant", "message": {"role": "assistant", "content": list(blocks)}}


def _result(tid, body):
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tid, "content": body}]}}


def _session():
    return [
        _user("SolveIt is on (the default). first prompt"),
        _assistant({"type": "text", "text": "It is the cause because id is nil."}),
        _user("second prompt"),
        _assistant(
            {"type": "text", "text": "Applied cleanly."},
            {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "bin/rails test x"}},
            {"type": "tool_use", "id": "t2", "name": "Write", "input": {"file_path": "/r/app.rb"}},
        ),
        _result("t1", "SolveIt: Bash runs task scripts + read-only search."),
    ]


def test_scan_counts_sessions_turns_edits_and_blocks(tmp_path):
    _transcript(tmp_path, "proj", _session())
    turns, blocks, bounced, sessions = health.scan(str(tmp_path), "2026-07-01")
    assert sessions == 1
    assert len(turns) == 2
    assert turns[1]["tools"] == 2 and turns[1]["edits"] == 1
    assert blocks["bash jail"] == 1
    assert bounced["bin/rails test"] == 1


def test_scan_skips_sessions_before_since(tmp_path):
    _transcript(tmp_path, "proj", _session())
    turns, _, _, sessions = health.scan(str(tmp_path), "2026-08-01")
    assert (sessions, turns) == (0, [])


def test_scan_ignores_transcripts_without_the_banner(tmp_path):
    _transcript(tmp_path, "proj", [_user("no banner here"), _assistant({"type": "text", "text": "hi"})])
    assert health.scan(str(tmp_path), "2026-07-01")[3] == 0


def test_task_script_writes_are_not_counted_as_project_edits(tmp_path):
    entries = _session()
    entries[3]["message"]["content"][2]["input"]["file_path"] = "/r/.solve/tasks/x/01.py"
    _transcript(tmp_path, "proj", entries)
    assert health.scan(str(tmp_path), "2026-07-01")[0][1]["edits"] == 0


def test_claim_turn_classification():
    assert health.is_claim_turn("It is the cause because id is nil.")
    assert not health.is_claim_turn("Which key do you mean?")
    assert not health.is_claim_turn("Applied cleanly.")
    assert not health.is_claim_turn("31 unstaged lines in the repo — stage what you accept.")
