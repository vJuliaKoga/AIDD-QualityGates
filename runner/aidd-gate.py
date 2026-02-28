import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml
from jsonschema import Draft202012Validator


def _substitute(obj: Any, ctx: Dict[str, Any]) -> Any:
    """Very small ${a.b.c} substitution for pack.yaml."""
    if isinstance(obj, str):
        def repl(m):
            key = m.group(1)
            cur = ctx
            for part in key.split("."):
                cur = cur.get(part, None) if isinstance(cur, dict) else None
                if cur is None:
                    return m.group(0)
            return str(cur)
        return re.sub(r"\$\{([^}]+)\}", repl, obj)
    if isinstance(obj, list):
        return [_substitute(x, ctx) for x in obj]
    if isinstance(obj, dict):
        return {k: _substitute(v, ctx) for k, v in obj.items()}
    return obj


@dataclass
class StepResult:
    step_id: str
    status: str  # PASS/WARN/FAIL
    details: Dict[str, Any]


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def gate_schema(step_id: str, target: Path, schema_file: Path) -> StepResult:
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    doc = load_yaml(target)
    errs = sorted(Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.path))
    if errs:
        return StepResult(step_id, "FAIL", {
            "target": str(target),
            "schema": str(schema_file),
            "errors": [{"path": list(e.path), "message": e.message} for e in errs],
        })
    return StepResult(step_id, "PASS", {"target": str(target), "schema": str(schema_file)})


def gate_ambiguity(step_id: str, targets: List[Path], dictionary_file: Path, severity_on_hit: str) -> StepResult:
    terms = []
    for line in dictionary_file.read_text(encoding="utf-8").splitlines():
        t = line.strip()
        if t and not t.startswith("#"):
            terms.append(t)

    findings = []
    for t in targets:
        text = t.read_text(encoding="utf-8")
        for term in terms:
            if term in text:
                findings.append({"file": str(t), "term": term})
    if findings:
        status = "FAIL" if severity_on_hit.lower() == "fail" else "WARN"
        return StepResult(step_id, status, {"dictionary": str(dictionary_file), "findings": findings})
    return StepResult(step_id, "PASS", {"dictionary": str(dictionary_file), "findings": []})


def gate_checklist(step_id: str, checklist: Path, fail_if_todo: bool, fail_if_abort_without_reason: bool, warn_if_abort_rate_over: float) -> StepResult:
    if not checklist.exists():
        return StepResult(step_id, "FAIL", {"error": f"checklist not found: {checklist}"})

    data = json.loads(checklist.read_text(encoding="utf-8"))
    items = data.get("items", [])
    if not isinstance(items, list):
        return StepResult(step_id, "FAIL", {"error": "checklist.items must be a list"})

    total = len(items)
    todo = 0
    abort = 0
    abort_no_reason = 0

    for it in items:
        status = (it.get("status") or "").lower()
        if status == "todo":
            todo += 1
        if status == "abort":
            abort += 1
            reason = (it.get("reason") or "").strip()
            if not reason:
                abort_no_reason += 1

    abort_rate = (abort / total) if total else 0.0

    # Decide status
    if fail_if_todo and todo > 0:
        return StepResult(step_id, "FAIL", {"total": total, "todo": todo, "abort": abort, "abort_no_reason": abort_no_reason, "abort_rate": abort_rate})
    if fail_if_abort_without_reason and abort_no_reason > 0:
        return StepResult(step_id, "FAIL", {"total": total, "todo": todo, "abort": abort, "abort_no_reason": abort_no_reason, "abort_rate": abort_rate})
    if abort_rate > warn_if_abort_rate_over:
        return StepResult(step_id, "WARN", {"total": total, "todo": todo, "abort": abort, "abort_no_reason": abort_no_reason, "abort_rate": abort_rate})

    return StepResult(step_id, "PASS", {"total": total, "todo": todo, "abort": abort, "abort_no_reason": abort_no_reason, "abort_rate": abort_rate})


def run_pack(pack_file: Path) -> Tuple[int, List[StepResult]]:
    pack = load_yaml(pack_file)
    ctx = {
        "paths": pack.get("paths", {}),
        "artifacts": pack.get("artifacts", {}),
        "schemas": pack.get("schemas", {}),
    }
    steps = pack.get("steps", [])
    steps = _substitute(steps, ctx)

    results: List[StepResult] = []
    for s in steps:
        sid = s["id"]
        kind = s["kind"]
        if kind == "schema":
            res = gate_schema(
                sid,
                Path(s["target"]),
                Path(s["schema"]),
            )
        elif kind == "ambiguity":
            res = gate_ambiguity(
                sid,
                [Path(p) for p in s.get("targets", [])],
                Path(s["dictionary"]),
                s.get("severity_on_hit", "warn"),
            )
        elif kind == "checklist_completion":
            res = gate_checklist(
                sid,
                Path(s["checklist"]),
                bool(s.get("fail_if_todo", True)),
                bool(s.get("fail_if_abort_without_reason", True)),
                float(s.get("warn_if_abort_rate_over", 0.3)),
            )
        else:
            res = StepResult(sid, "FAIL", {"error": f"unknown kind: {kind}"})

        results.append(res)

    # overall exit code
    exit_code = 0
    if any(r.status == "FAIL" for r in results):
        exit_code = 2
    elif any(r.status == "WARN" for r in results):
        exit_code = 1

    return exit_code, results


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True, help="pack yaml path, e.g., packs/pln_pack/pln.pack.yaml")
    ap.add_argument("--outdir", default="output", help="output dir")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    exit_code, results = run_pack(Path(args.pack))
    report = {
        "pack": args.pack,
        "exit_code": exit_code,
        "results": [{"step_id": r.step_id, "status": r.status, "details": r.details} for r in results],
    }
    write_json(outdir / "pln_gate_report.json", report)

    # Print human-readable summary
    for r in results:
        print(f"[{r.status}] {r.step_id}")
        if r.status != "PASS":
            print(json.dumps(r.details, ensure_ascii=False, indent=2))

    # 重要: CI の場合、ビルドを続行するには WARN で 0 を返します。
    # ここでは、FAIL の場合は 2 を返し、それ以外の場合は 0 を返します (警告はレポートに表示されます)。
    sys.exit(2 if exit_code == 2 else 0)


if __name__ == "__main__":
    main()
