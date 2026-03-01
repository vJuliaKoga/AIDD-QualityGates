$ErrorActionPreference = "Stop"

# ---- DeepEval timeout延長（精度は変えずに時間だけ伸ばす）----
$env:DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE = "900"
# $env:DEEPEVAL_LOG_STACK_TRACES = "1"   # 必要なら
# $env:DEEPEVAL_DISABLE_TIMEOUTS = "1"  # 最終手段（ハング注意）

$env:AIDD_STAGE = "PLN"
$env:AIDD_REF_MODE = "MD"
$env:AIDD_MD_PATH = "artifacts\planning\PLN-PLN-FLW-002.md"
$env:AIDD_YAML_DIR = "artifacts\planning\yaml\v3"

# 変換品質は整合性（CONSIST）
$env:AIDD_CHECKLISTS = "packs\checklists\CHK-PLN-CONSIST-001.yaml"

$env:AIDD_OUT_ROOT = "output\G4\pln_transform"

$env:AIDD_EVAL_MODEL = "gpt-5.2"

python .\runner\gates\g4_deepeval.py