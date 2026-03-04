$ErrorActionPreference = "Stop"

# Confident AI を完全に無効化（保険）
$env:AIDD_ENABLE_CONFIDENT = "0"
$env:DEEPEVAL_DISABLE_DOTENV = "1"
$env:DEEPEVAL_DISABLE_CONFIDENT = "1"

# ---- DeepEval timeout延長 ----
$env:DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE = "900"

$env:AIDD_STAGE = "PLN"
$env:AIDD_REF_MODE = "AUTO"
$env:AIDD_REF_PATHS = "artifacts\planning\PLN-PLN-FLW-003.md"
$env:AIDD_YAML_DIR = "artifacts\planning\yaml\PLN-PLN-FLW-003"

$env:AIDD_OUT_ROOT = "output\G4\pln_transform"
$env:AIDD_EVAL_MODEL = "gpt-5.2"

# Faithfulness安定化
$env:AIDD_FAITHFULNESS_ACTUAL_MAX_CHARS = "1800"
$env:AIDD_FAITHFULNESS_CONTEXT_MAX_CHARS = "2200"
$env:AIDD_FAITHFULNESS_TRUTHS_LIMIT = "10"
$env:AIDD_FAITHFULNESS_RETRY_ON_TIMEOUT = "1"
$env:AIDD_FAITHFULNESS_ACTUAL_MAX_CHARS_RETRY = "1200"
$env:AIDD_FAITHFULNESS_CONTEXT_MAX_CHARS_RETRY = "1600"
$env:AIDD_FAITHFULNESS_TRUTHS_LIMIT_RETRY = "6"

# 007版のタイムアウト耐性（推奨）
$env:AIDD_FAITHFULNESS_TOPK_REF_CHUNKS = "3"
$env:AIDD_FAITHFULNESS_REF_CHUNK_MAX_CHARS = "800"

# derived_from が未整備でSKIPばかりになるなら0
# $env:AIDD_FAITHFULNESS_SKIP_DERIVED_FROM_SCOPE = "0"

# Coverage/Consistency ノイズ低減（Run-2推奨）
$env:AIDD_COVERAGE_SKIP_HEADINGS = "1"
$env:AIDD_CONSISTENCY_IGNORE_KEYS = "meta.,timestamp,updated_at,created_at,hash,checksum,rationale,ssot_note,primary_section,traceability.,referenced_internal_ids"

python .\runner\gates\g4_deepeval.py