---
meta:
  artifact_id: PRM-PLN-G4-FIX-002
  file: PRM-PLN-G4-FIX-002.md
  author: "@juria.koga"
  source_type: human
  source: manual
  timestamp: "2026-03-03T17:43:00+09:00"
  content_hash: 96178a6ab68193ab9ab725128b4e0269bccc365ee88304a3706568e31d808573
---

## 修正依頼プロンプト（PRM-PLN-G4-FIX-002）

あなたはAIDD Score Aggregation Managersの **企画MD→企画YAML整形担当**です。
以下の入力を必ず読み、**Run-1（pln_transform）で落ちた原因（欠落/矛盾/誤変換、特に参照にない断定の混入）を解消するように、企画YAMLを修正**してください。

### 入力（必ず読む）

1. 参照元（企画MD）

- `artifacts\planning\PLN-PLN-FLW-003.md`

2. DeepEval出力JSON（最新Run-1）

- `output\G4\pln_transform\artifacts_planning_yaml_PLN-PLN-FLW-003\0303_1730.json`

3. 評価対象（企画YAML分割）

- `artifacts/planning/yaml/PLN-PLN-FLW-004/` 配下のYAML一式
  - 特に優先対象:
    - `PLN-PLN-DES-002.yaml`
    - `PLN-PLN-DES-006.yaml`
    - `PLN-PLN-YAML-001.yaml`

  - ただし他ファイルも、MDと照らして参照にない断定や不足があれば修正すること。

4. 既存の評価レポート（今回作成済みのRun-1レポート本文）

- `output\G4\reports\pln_transform\RES-PLN-TRANS-005.md`

---

### 目的（この修正で必ず満たすこと）

- 企画MDの内容が、企画YAMLに **「欠落なく」「矛盾なく」「誤った言い換えなく」** 落ちている状態にする
- **MDに書かれていない内容（推測・補完・閾値・運用ルール・具体例・出力フィールドの断定）をYAML本文として混入させない**
- 分割YAMLとして自然に異なる情報（例: rationale/ssot_note/primary_section 等）で、**“矛盾”を生まない書き方**にする（可能なら比較キーになりやすい断定表現を弱める）

---

### 修正方針（厳守）

- **SSOTはMD**。MDに無い情報は「本文」には書かない
- どうしても将来の提案として残したい場合は、本文とは別の明確な枠に隔離すること
  - 例: `ai_suggestion:` / `proposal:` / `notes_non_ssot:` のようなキーを新設して分離
  - ただし、DeepEvalのFaithfulness対象になりそうな位置（本文扱い）に入れない

- 数値閾値・条件・具体例・チェック方法の割当などは、**MDに明記がない限り削除 or TBD扱い**
- MDの文章を要約する場合も、意味が変わる言い換えは禁止（特に条件・閾値・必須/任意の強さ）

---

### 優先して直すべき具体論点（必須対応）

#### 1) `PLN-PLN-DES-002.yaml`

- Gate仕様で、MDに無い **warning帯/pass帯の閾値**、**出力fieldsの断定**、**条件の細分化** があれば削除またはMD記載粒度へ戻す
- MDに明記されている「即時失格条件」等は保持する（例: G1=10件超、G4=0.6未満 など、MDにある範囲）

#### 2) `PLN-PLN-DES-006.yaml`

- `risk_level_declaration.default: HIGH` のような **未宣言時デフォルト規則**は、MDに根拠が無ければ削除 or TBD化

#### 3) `PLN-PLN-YAML-001.yaml`

- `pln_pack_mandatory_qa` で、MDに無い **check_method / pass_criterion / fail_example / pass_example** などの断定要素は削除し、MDにある「3観点の列挙と説明」程度へ戻す

---

### 追加チェック（できる範囲で実施）

- DeepEval JSONの Coverage / Consistency の “未カバー”“contradictions” を見て、
  - **本当にMD欠落なのか**
  - **照合設計由来のノイズなのか**
    を判断し、YAML本文側で解消できる「明らかな欠落」だけ直す

- ただし **見出し文字列をそのままYAMLに増やしてCoverageを稼ぐ**ような対処は禁止（MDの意味構造を壊すので）

---

### 出力要件（厳守）

1. 変更したYAMLは`artifacts\planning\yaml\PLN-PLN-FLW-004`内のyamlに上書きしてを出力すること（差分だけ不可）
2. `変更概要`（箇条書き、どのファイルのどのキーを、なぜ修正したか）各項目にMD根拠を添えること。
3. 変更概要には必ず以下を含める
   - 対象ファイル名
   - 修正したセクション（キー階層）
   - 修正内容（削除/弱化/TBD化/移設 等）
   - 根拠（MDの該当箇所の短い引用または要約）
   - DeepEvalでの問題点（0303_1730.jsonのどの観点に効く修正か：Faithfulness/Coverage/Consistency）

---

### 禁止

- MDに書かれていない一般論・推測・勝手な仕様補完の追加
- 「本来こうあるべき」など、参照外の設計思想での断定
- YAMLの目的（分割・要点整理）を逸脱した過剰な再構成

---

### 最低限の期待成果

- `PLN-PLN-DES-002.yaml / DES-006.yaml / YAML-001.yaml` は、MDに無い断定要素が除去されていること
- 可能なら、Run-1のFaithfulnessが改善する方向（参照外情報の混入が減る）になっていること

---

必要なら、上のプロンプト末尾にこの一文も足すとより安定します：

> 「MDに根拠がない場合は “削除” を第一選択にし、どうしても残すなら `notes_non_ssot` 等に隔離し、本文扱いのキーには入れないでください。」

---
