$ErrorActionPreference = "Stop"

# Confident AI を完全に無効化（保険）
$env:AIDD_ENABLE_CONFIDENT = "0"
$env:DEEPEVAL_DISABLE_DOTENV = "1"     # .env.local を読ませない
$env:DEEPEVAL_DISABLE_CONFIDENT = "1"  # Confident連携を止める

# ---- DeepEval timeout延長（精度は変えずに時間だけ伸ばす）----
$env:DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE = "900"
# $env:DEEPEVAL_LOG_STACK_TRACES = "1"   # 必要なら
# $env:DEEPEVAL_DISABLE_TIMEOUTS = "1"  # 最終手段（ハング注意）

$env:AIDD_STAGE = "PLN"
$env:AIDD_REF_MODE = "MD"
$env:AIDD_MD_PATH = "artifacts\planning\PLN-PLN-FLW-002.md"
$env:AIDD_YAML_DIR = "artifacts\planning\yaml\v3"

# 充足はAIDDチェックリスト
$env:AIDD_CHECKLISTS = "packs\checklists\CHK-PLN-AIDD-001.yaml"

$env:AIDD_OUT_ROOT = "output\G4\pln_coverage"

$env:AIDD_EVAL_MODEL = "gpt-5.2"

# Faithfulness評価から除外するファイル名（カンマ区切り）
# 理由: coverage実行はAIDDチェックリスト充足の確認が目的のため、
#       Faithfulness評価は全スキップしてChecklist評価のみを実施する
$env:AIDD_FAITHFULNESS_SKIP = "*"

python .\runner\gates\g4_deepeval.py