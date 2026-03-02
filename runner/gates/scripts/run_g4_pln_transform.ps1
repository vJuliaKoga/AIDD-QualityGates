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

# 変換品質は整合性（CONSIST）
$env:AIDD_CHECKLISTS = "packs\checklists\CHK-PLN-CONSIST-001.yaml"

$env:AIDD_OUT_ROOT = "output\G4\pln_transform"

$env:AIDD_EVAL_MODEL = "gpt-5.2"

# Faithfulness評価から除外するファイル名（カンマ区切り）
# 理由: 主参照MD（PLN-PLN-FLW-002.md）以外のMDを derived_from に持つ補足事項ファイルを明示除外
# ※ is_qa_supplement() ヒューリスティックでも自動検出されるが、意図を明示するため記載する
$env:AIDD_FAITHFULNESS_SKIP = "PLN-PLN-AIQUA-002.yaml"

python .\runner\gates\g4_deepeval.py