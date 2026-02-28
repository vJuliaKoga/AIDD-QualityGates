import json
import subprocess
from pathlib import Path

import allure


REPO_ROOT = Path(__file__).resolve().parents[1]


@allure.suite("PLN Pack CI Minimal")
def test_pln_pack_gates():
    pack = REPO_ROOT / "packs" / "pln_pack" / "pln.pack.yaml"
    outdir = REPO_ROOT / "output"
    outdir.mkdir(exist_ok=True)

    cmd = ["python", str(REPO_ROOT / "runner" / "aidd_gate.py"), "--pack", str(pack), "--outdir", str(outdir)]
    p = subprocess.run(cmd, capture_output=True, text=True)

    allure.attach(p.stdout, name="runner_stdout", attachment_type=allure.attachment_type.TEXT)
    allure.attach(p.stderr, name="runner_stderr", attachment_type=allure.attachment_type.TEXT)

    report_file = outdir / "pln_gate_report.json"
    assert report_file.exists(), "pln_gate_report.json was not generated"

    report = json.loads(report_file.read_text(encoding="utf-8"))
    allure.attach(json.dumps(report, ensure_ascii=False, indent=2), name="pln_gate_report", attachment_type=allure.attachment_type.JSON)

    # FAILならここで落ちる（runnerはFAIL時exit 2）
    assert p.returncode == 0, f"Gate runner failed (exit={p.returncode}). See attachments."