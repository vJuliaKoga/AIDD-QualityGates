---
meta:
  artifact_id: RES-PLN-G4-REVIEW-001
  file: RES-PLN-G4-REVIEW-001.md
  author: gpt-5.2
  source_type: ai
  source: Cline
  prompt_id: PRM-PLN-TRANS-001
  timestamp: "2026-03-07T10:25:00+09:00"
  model: gpt-5.2
  content_hash: 1901b4af1d299a5b95aa4ccfa0b2ce6805878cd21824116a8db898cbf23e485f
---

# 改善バックログ（G4 / PLN Deep Eval）— 2026-03-07 01:55 実行結果ベース

## 0. 目的

- Faithfulness の大量FAILを「SSOT不足（参照MDが薄い）」と「評価条件（拾い方/表現ゆれ）」に分離し、短いサイクルで改善する。
- Coverage / Consistency は “精度を上げる” 方向でノイズを削り、信頼できる指標に寄せる。

## 1. 状況サマリ（今回の実行）

- 総テスト: 24 / 合格: 2 / 総合: FAIL
- Faithfulness: 22件すべて FAIL（平均 ~0.215）
- Coverage(GLOBAL): PASS（80件中 75件カバー）
- Consistency(GLOBAL): PASS（ただし矛盾4件＝うちノイズが多い）

---

## 2. P0（最優先 / “次のRunで数字が動く”）

### P0-1. FaithfulnessのSSOT不足を解消（YAML→MD逆輸入）

**方針**: 「YAMLの方が正しい/必要」なら、対応する split MD（derived_from のMD）へ根拠として追記してSSOTを更新する。  
**Done条件**: 対象ファイルの Faithfulness が 0.15以上改善、または FAIL理由が“表現ゆれ”へ収束。

#### 対象（スコア下位から着手）

- [ ] `PLN-PLN-TRACEABILITY-001`（score 0.0000）
  - split MDに追記: 目的 / 粒度 / 出力例 / 紐付けルール（最低3〜5 bullet）
- [ ] `PLN-PLN-CHECKLIST-001`（0.1111）
  - split MDに追記: チェック観点を “YAMLのキー/用語” に合わせて bullet化
- [ ] `PLN-PLN-ROADMAP-001`（0.1515）
- [ ] `PLN-PLN-ALLURE-001`（0.1633）
- [ ] `PLN-PLN-GOAL-001`（0.1667）
- [ ] `PLN-PLN-USER-001`（0.1795）
- [ ] `PLN-PLN-EXEC-001`（0.1837）
- [ ] `PLN-PLN-SOLUTION-001`（0.1837）
- [ ] `PLN-PLN-CFUI-001`（0.2000）
- [ ] `PLN-PLN-SCOREPOLICY-001`（0.2093）
- [ ] `PLN-PLN-IDISSUANCE-001`（0.2222）

> 追記の粒度（テンプレ）
>
> - 章の見出し（1行）
> - bullet 3〜5個（YAMLの主要キーに対応）
> - 例（可能なら1つ）
> - 決定/根拠があるなら（決定日 or 出典）を1行

---

### P0-2. “異常に遅い” Faithfulness を軽くする（評価の安定化）

**狙い**: 1ファイルに8分近くかかっている個体を潰し、全体サイクルを短縮する。  
**Done条件**: 対象ファイルの `duration_ms` が半減（目安 < 240,000ms）またはリトライ発生が減る。

#### 対象（duration上位）

- [ ] `PLN-PLN-SCOREPOLICY-001`（~489s）
- [ ] `PLN-PLN-PACK-001`（~480s）
- [ ] `PLN-PLN-IDISSUANCE-001`（~473s）

#### 具体施策（上から順に）

- [ ] split MD側に “YAMLが主張する核心bullet” を追加（参照が薄いと推論が長引きやすい）
- [ ] YAML側で長文説明を「箇条書き化」して `actual_output` の密度を上げる（長文だと評価が重い）
- [ ] それでも重い場合のみ（Run-2以降）
  - [ ] `AIDD_FAITHFULNESS_TOPK_REF_CHUNKS=2` に下げる
  - [ ] `AIDD_FAITHFULNESS_REF_CHUNK_MAX_CHARS=650` に下げる

---

## 3. P1（品質を“正しく”測るための調整）

### P1-1. Coverage 未カバー 5件の解消（見出しだけ問題＆用語不一致）

**Done条件**: 未カバー 5 → 0（または 1以下）

- [ ] 「重み付き合算スコア…（9.3節）…」
  - YAML側に “重み/合算/総合得点” の語を含むキー or 説明を追記（またはMD側の表現をYAML寄せ）
- [ ] 「CheckFlowの出力JSONをGate Runnerが消費…フォーマット早期確定…」
  - split MDに bullet 1〜2個で中身を書いてしまう（現状マッチ0）
- [ ] 「UIコンポーネント構成：」
  - split MDで “：だけ” をやめて bullet 1行追加（論点抽出が安定する）
- [ ] 「JSONデータ構造設計：」
  - 同上（bullet 1行）
- [ ] 「humanreview」
  - YAML側にタグ/キーとして `humanreview` を入れる、またはMD側の語を統一（別表現に置換）

---

### P1-2. Consistency の“ノイズ矛盾”を抑制（見たい矛盾だけ残す）

**Done条件**: “仕様的に正常”な矛盾が出なくなる（derived_from / artifact_kind が矛盾一覧から消える）

- [ ] `AIDD_CONSISTENCY_IGNORE_KEYS` に以下を追加
  - `derived_from`
  - `artifact_kind`
- [ ] `changes` の扱いを統一
  - A案: 全ファイル必須（空でも良いので文字列）
  - B案: 任意扱いにして consistency 比較から除外（ignoreに入れる）

---

### P1-3. numeric_mismatch（pass: 70/90混入）を解消

**Done条件**: `pass` の observed から `70, 90` が消える

- [ ] 閾値表現を統一
  - 小数（例: 0.7）に統一するなら、%表記（70/90）を YAML から追放して別キーへ（例: `pass_percent`）
  - %表記を残すなら、参照MD側の記述も % に寄せる（ただし現状は小数が期待値にいる）

---

## 4. P2（将来の運用をラクにする）

### P2-1. “YAML→MD逆輸入”の運用ガイド整備

**Done条件**: 逆輸入の判断基準とテンプレが1ページで共有できる

- [ ] 逆輸入ルール（例）
  - 「YAMLが正しい」= 決定済み/合意済み/別資料に根拠あり → MDへ追記
  - 「まだ仮説」= （案）（要検討）ラベルでMDへ追記
- [ ] 追記テンプレ（見出し + bullet 3〜5 + 例 1つ）

---

### P2-2. “表現ゆれ辞書”の導入（coverage/faiの底上げ）

**Done条件**: よくある同義語のズレが原因のFAILが減る

- [ ] 用語揺れ（例: 総合得点/合算スコア/weighted score など）を辞書化
- [ ] split MDの用語をYAML寄せに統一（もしくはYAMLに別名を併記）

---

## 5. 次のRun（推奨手順）

1. P0-1 をまず 3ファイル（TRACEABILITY/CHECKLIST/ROADMAP）で実施 → 再実行
2. まだ全滅なら、P0-2（重い3ファイル）を重点的に split MD 追記 → 再実行
3. P1（coverage未カバー＆consistencyノイズ）で計測の信頼性を上げる

---
