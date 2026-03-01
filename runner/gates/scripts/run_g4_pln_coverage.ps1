$ErrorActionPreference = "Stop"

# ---- DeepEval timeout延長（精度は変えずに時間だけ伸ばす）----
$env:DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE = "900"
# $env:DEEPEVAL_LOG_STACK_TRACES = "1"   # 必要なら
# $env:DEEPEVAL_DISABLE_TIMEOUTS = "1"  # 最終手段（ハング注意）

$env:AIDD_STAGE = "PLN"
$env:AIDD_REF_MODE = "YAML"

# 参照は企画YAML（SSOT）。評価対象も同じ企画YAMLで（観点充足の自己チェック）
$env:AIDD_REF_YAML_DIR = "artifacts\planning\yaml"
$env:AIDD_YAML_DIR = "artifacts\planning\yaml"

# 充足はAIDD
$env:AIDD_CHECKLISTS = "packs\checklists\CHK-PLN-AIDD-001.yaml"

$env:AIDD_OUT_ROOT = "output\G4\pln_coverage"

python .\runner\gates\g4_deepeval.py