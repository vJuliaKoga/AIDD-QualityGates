---
meta:
  artifact_id: PRM-PLN-YAML-001
  file: PRM-PLN-YAML-001.md
  author: "@juria.koga"
  source_type: human
  source: manual
  timestamp: "2026-03-03T21:29:00+09:00"
  content_hash: e88dbb9577d2702d7fe0f66b2cfacdc5d4f35c77a35a8749ae2a06060f072f4c
---

あなたは「Markdown企画文書（MD）」から情報を**抽出して構造化**し、指定のYAMLスキーマ（テンプレ構造）に**厳密一致**させて保存する編集者です。**MD本文の丸ごと貼り付けは禁止**です。**スクリプト作成・実行は禁止**です。

### 入力

- MD: `artifacts/planning/PLN-PLN-SPLIT-001/` 配下の全 `.md`
- YAMLテンプレ（スキーマの正）：後でユーザーが貼る「本来のテンプレ構成」（現時点では下記のキー構成を厳守）

### 出力

- 出力先: `artifacts/planning/yaml/`
- 各MDにつきYAML 1つ。ファイル名はMDと同名（`.yaml`）

---

## 絶対禁止

1. **本文コピペ禁止**

- `primary_section` や他フィールドに、MD本文・表・段落をそのまま貼り付けない。
- MDからやるのは「抽出→要点を構造化（箇条書き/キー値/配列化）」のみ。

2. **frontmatter（`--- meta: ... ---`）の転記禁止**

- MD先頭の `---` で囲まれたメタブロックは本文ではない。YAMLへ貼らない。

3. **スクリプト禁止**

- 新規ファイル作成は `artifacts/planning/yaml/*.yaml` のみ。
- 変換ツール、Python/Node/シェル、実行、インストール提案、全部禁止。

4. **スキーマ厳密一致**

- 出力YAMLは以下のキー構造に**完全一致**（追加・削除・別名禁止、ネストも同様）。
- 値が作れない場合は `null` のままでよい（ただしキーは必ず出す）。

* artifacts\planning\pln_canonical_template_v1.yaml

---

## 必須の作り方（“考えて書く”部分）

### A) meta の埋め方（推測しない範囲で）

- `meta.artifact_id`: MDのID（ファイル名由来の `PLN-PLN-XXX-001`）
- `meta.file`: 出力YAMLファイル名
- `meta.author/source_type/source/prompt_id/model/timestamp/content_hash`: **MDや作業ログに明示がなければ null のまま**（勝手に gpt-5.2 とか書かない）
- `meta.schema_version`: そのまま `pln_canonical_template_v1`

### B) derived_from

- MD本文に「derived_from / 出典」が明示されていれば埋める
- 無ければ null（ファイル名から推測しない）

### C) primary_section の意味（重要）

- `primary_section` は **“本文貼り付け場所”ではない**。
- ここには **抽出元の見出し名（短い文字列）だけ**を入れる。例：
  - `"0. エグゼクティブサマリー"`
  - `"16. 配布形態（社内展開：Phase 1 はサーバー不要）"`

- 本文は入れない。

### D) artifact_kind の決め方（ファイル名 or 内容の明示に基づく）

- ファイル名の目的語（例：`PLN-PLN-CONS-001` → constraints）に対応できるならそれを採用
- 対応が曖昧なら、MDに明示されている目的（例：「制約」「目的」「スコープ」等）に従う
- どちらも曖昧なら null（推測で決めない）

### E) 本体セクション（goal/problem/scope/constraints…）の埋め方

- `artifact_kind` に対応するセクション（例：constraints なら `constraints:`）だけを**構造化して埋める**
- それ以外のセクションは null のままでOK（無理に埋めない）
- 構造化ルール：
  - 表は「配列の要素」にする（行を item 化）
  - 文章は「箇条書きの配列」か「短いキー値」に分解する
  - **MDの表現を保ったまま**（一般論で言い換えない）
  - ただし **丸写し段落は禁止**：必ず分解して短文化する

### F) rationale / ssot_note（要点だけ）

- `rationale`: 「どの見出しから何を抽出したか」を短く書く（1〜5行程度）
- `ssot_note`: “このYAMLがSSOT”など運用メモがMDに書かれていれば転記。無ければ null
- ここに「後でメタ付ける予定」みたいな文章は書かない（読みたくないため）

### G) CFUI-001 の混在（要件/基本設計）

- 分類用の新規キーは作らない
- “混在している”説明文も入れない
- 代わりに、MD内の「要件定義用」「基本設計用」などの文言は、抽出した項目のラベルとして**同じ語をそのまま**使って構造化する
  例：`items: [{label: "要件定義用", ...}, {label: "基本設計用", ...}]` のように、既存キー内で表現（新規トップレベルキーは禁止）

---

## 仕上げチェック（必須）

各YAMLについて必ず確認してから保存：

- トップレベルキーが上のテンプレと**完全一致**（増減なし）
- `primary_section` に本文が入っていない（短い見出しだけ）
- MD本文の丸ごと貼り付けがない
- frontmatter を転記していない
- `artifact_kind` と対応セクションだけが埋まっている（他は null でもOK）
- 余計な推測（モデル名やtimestamp等）を書いていない

---

## チャット報告（最後にこれだけ）

- 生成したYAMLファイル一覧（パス付き）
- どのセクション（goal/problem/…）を埋めたかを各ファイル1行で

---
