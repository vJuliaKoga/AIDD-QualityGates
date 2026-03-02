$ErrorActionPreference = "Stop"

# Confident AI を完全に無効化（保険）
$env:AIDD_ENABLE_CONFIDENT = "0"
$env:DEEPEVAL_DISABLE_DOTENV = "1"     # .env.local を読ませない
$env:DEEPEVAL_DISABLE_CONFIDENT = "1"  # Confident連携を止める

# ---- DeepEval timeout延長（時間だけ伸ばす）----
$env:DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE = "900"
# $env:DEEPEVAL_LOG_STACK_TRACES = "1"   # 何かあった時だけ
# $env:DEEPEVAL_DISABLE_TIMEOUTS = "1"  # 最終手段（ハング注意）

$env:AIDD_STAGE = "PLN"
$env:AIDD_REF_MODE = "AUTO"     # 参照ファイルの拡張子で自動判定
$env:AIDD_FILE_PATH = "artifacts\planning\PLN-PLN-FLW-002.md"
$env:AIDD_YAML_DIR = "artifacts\planning\yaml\v3"

# 変換品質は整合性（CONSIST）
$env:AIDD_CHECKLISTS = "packs\checklists\CHK-PLN-CONSIST-001.yaml"

$env:AIDD_OUT_ROOT = "output\G4\pln_transform"

$env:AIDD_EVAL_MODEL = "gpt-5.2"

# Faithfulness安定化（当面ON推奨）
# もし将来「もっと厳密に見たい」タイミングが来たら、段階的に戻す
# 例）ACTUAL_MAX_CHARS=2500 → 3500、CONTEXT_MAX_CHARS=3000 → 4500、TRUTHS_LIMIT=16 → 20

$env:AIDD_FAITHFULNESS_ACTUAL_MAX_CHARS = "2000"
$env:AIDD_FAITHFULNESS_TRUTHS_LIMIT = "12"
$env:AIDD_FAITHFULNESS_CONTEXT_MAX_CHARS = "2500"

python .\runner\gates\g4_deepeval.py