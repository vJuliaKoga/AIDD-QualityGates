「QA4AIDD Gate + Coach」v3.0

エグゼクティブサマリー（改訂）

``┌─────────────────────────────────────────────────────────────────┐
│  AI活用開発（AIDD）の品質保証を「自動ゲート」と「人の判断」の    │
│  2層で担保し、"動けばOK"から"説明できる品質"へ転換する基盤      │
└─────────────────────────────────────────────────────────────────┘`

コア価値（3行で伝える）

| 役割       | 担当     | 実現手段                          |
| ---------- | -------- | --------------------------------- |
| 判断       | 人       | Coach UI（Done/Abort + 理由記録） |
| 検証       | 自動     | Gate Runner（Docker/CLI）         |
| 記憶・証跡 | システム | JSON出力 → Allure集約             |

課題の再定義（Why Now?）
2.1 現状の構造的問題

`上流の曖昧さ ──→ 中流で矛盾蓄積 ──→ 下流で爆発（手戻りコスト10倍）
     ↑
  ここで止めたい`

2.2 社内で解くべき3つの課題

| #   | 課題             | 現象                                   | 本企画の解法                     |
| --- | ---------------- | -------------------------------------- | -------------------------------- |
| 1   | QA観点の属人化   | 初学者が「何を見ればいいか」分からない | Coach UIで観点をチュートリアル化 |
| 2   | 品質観点の後回し | 企画段階で品質が議論されない           | 工程パック（PLNから導入）        |
| 3   | 責任の不明確化   | 「誰が判断したか」が残らない           | Done/Abort + User + Timestamp    |

ソリューション全体像（改訂）

`┌────────────────────────────────────────────────────────────────────┐
│                        QA4AIDD Gate + Coach                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   ┌──────────────┐      JSON出力      ┌──────────────────────┐    │
│   │  Coach UI    │ ─────────────────→ │   CI/Runner          │    │
│   │（人の判断）   │   checklist.json   │  （自動検証）         │    │
│   │              │                    │                      │    │
│   │ ・工程タブ    │                    │ ・Gate Runner実行    │    │
│   │ ・動的展開    │                    │ ・JSON読込＆検証     │    │
│   │ ・Done/Abort │                    │ ・Allure出力         │    │
│   └──────────────┘                    └──────────────────────┘    │
│          │                                      │                  │
│          └──────────────┬───────────────────────┘                  │
│                         ▼                                          │
│              ┌──────────────────────┐                              │
│              │   Allure Report      │                              │
│              │ ・自動ゲート結果     │                              │
│              │ ・人の判断ログ       │                              │
│              │ ・統合ダッシュボード │                              │
│              └──────────────────────┘                              │
└────────────────────────────────────────────────────────────────────┘`

Coach UI 詳細設計（動的チェックリスト）
4.1 画面フロー

`┌─────────────────────────────────────────────────────────────┐
│  [企画] [要件] [基本設計] [詳細設計] [実装] [テスト]        │  ← 工程タブ
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ▼ REQ-001: 要件の検証可能性                    [Todo ▼]   │  ← L2タスク
│  ┌─────────────────────────────────────────────────────┐   │
│  │  📋 観点：要件は測定可能な言葉で記述されているか    │   │  ← L3展開
│  │  ──────────────────────────────────────────────     │   │
│  │  ✓ チェック項目：                                   │   │
│  │    □ 「〜を向上」ではなく「〜を20%向上」のように    │   │
│  │      定量化されている                               │   │
│  │    □ 曖昧語（適切に、なるべく等）が排除されている  │   │
│  │                                                     │   │
│  │  📎 参照：CHK-REQ-REVIEW-001 / evalcriteria        │   │
│  │  🤖 Deep Eval: verifiabilityprompt.yaml            │   │
│  │                                                     │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────────────────┐   │   │
│  │  │  Done   │ │  Abort  │ │ 理由（Abort時必須）│   │   │
│  │  └─────────┘ └─────────┘ └─────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ▶ REQ-002: AIプロンプト可読性                  [Locked]   │  ← 次項目
│  ▶ REQ-003: トレーサビリティ確保               [Locked]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘`

4.2 状態遷移

`              ┌─────────────────────────────────┐
              │                                 │
              ▼                                 │
┌──────┐   クリック   ┌──────────┐            │
│ Todo │ ──────────→ │ 展開中   │            │
└──────┘              └──────────┘            │
                           │                   │
              ┌────────────┴────────────┐     │
              ▼                         ▼     │
        ┌──────────┐              ┌──────────┐│
        │   Done   │              │  Abort   ││
        │          │              │(理由必須)││
        └──────────┘              └──────────┘│
              │                         │     │
              └─────────┬───────────────┘     │
                        ▼                     │
                  次項目Unlock ───────────────┘`

4.3 JSON出力仕様

`json
{
  "meta": {
    "projectid": "PRJ-2025-001",
    "phase": "REQ",
    "generatedat": "2025-01-15T10:30:00+09:00",
    "toolversion": "1.0.0"
  },
  "checklistresults": [
    {
      "id": "CHK-REQ-001",
      "title": "要件の検証可能性",
      "status": "Done",
      "checkedby": "tanaka.taro",
      "timestamp": "2025-01-15T10:25:30+09:00",
      "reason": null,
      "evidencerefs": ["REQ-FUNC-001", "REQ-FUNC-002"]
    },
    {
      "id": "CHK-REQ-002",
      "title": "AIプロンプト可読性",
      "status": "Abort",
      "checkedby": "tanaka.taro",
      "timestamp": "2025-01-15T10:28:15+09:00",
      "reason": "Phase2スコープとしてステークホルダー合意済み（MTG: 2025-01-10）",
      "evidencerefs": []
    }
  ],
  "summary": {
    "total": 12,
    "done": 10,
    "abort": 2,
    "completionrate": 1.0
  }
}
`

Gate Runner詳細設計（Docker/CLI）
5.1 ゲート一覧（工程横断）

| Gate ID | 検証内容                 | 入力                    | 出力                     |
| ------- | ------------------------ | ----------------------- | ------------------------ |
| G1      | 曖昧語チェック           | .yaml, .md              | ambiguityreport.json     |
| G2      | Checklist完了検証（New） | checklist.json          | checklistvalidation.json |
| G3      | Schema検証               | \*.yaml                 | schemareport.json        |
| G4      | Deep Evalスコアリング    | prompts/, requirements/ | deepevalscores.json      |
| G5      | トレーサビリティ         | 全ID参照                | tracematrix.json         |
| PF      | Promptfoo評価            | prompts/                | promptfooresults.json    |

5.2 G2: Checklist完了検証（④の実現）

ポイント：「JSON読込でビルドPass/Fail」は実現可能

`yaml
gateg2checklistvalidator.yaml
name: "Checklist Completion Gate"
description: "Coach UIからのJSON出力を検証し、ビルド可否を判定"

validationrules:

# 必須：全項目がDoneまたはAbort（Todoが残っていたらFail）

- rule: "notodoremaining"
  condition: "all items.status in ['Done', 'Abort']"
  severity: "blocker"

# 必須：Abortには必ず理由がある

- rule: "aborthasreason"
  condition: "if status == 'Abort' then reason != null"
  severity: "blocker"

# 警告：Abort率が高すぎる場合

- rule: "abortratethreshold"
  condition: "abortcount / totalcount < 0.3"
  severity: "warning"
  message: "Abort率が30%を超えています。スコープ再検討を推奨"

exitcodes:
success: 0 # 全検証Pass → CI続行
warning: 1 # 警告あり → CI続行（レポート出力）
failure: 2 # blocker検出 → CI停止
`

5.3 Docker構成

`dockerfile
Dockerfile.gaterunner
FROM python:3.11-slim

WORKDIR /app

依存関係
COPY requirements.txt .
RUN pip install -r requirements.txt

ゲートスクリプト
COPY gates/ ./gates/
COPY schemas/ ./schemas/
COPY entrypoint.sh .

入力・出力マウントポイント
VOLUME ["/input", "/output", "/allure-results"]

ENTRYPOINT ["./entrypoint.sh"]
CMD ["--phase", "REQ", "--gates", "G1,G2,G3,G5"]
`

`bash
実行例（ローカル）
docker run -v $(pwd)/artifacts:/input \
 -v $(pwd)/output:/output \
 -v $(pwd)/allure-results:/allure-results \
 qa4aidd-gate:latest --phase REQ --gates G1,G2,G3

CI実行例（GitHub Actions）
• name: Run QA Gates
run: |
docker run -v ${{ github.workspace }}/artifacts:/input \
 -v ${{ github.workspace }}/output:/output \
 qa4aidd-gate:latest --phase REQ

• name: Check Gate Results
run: |
if [ $(cat output/gatesummary.json | jq '.exitcode') -ne 0 ]; then
echo "Quality Gate Failed"
exit 1
fi
`

工程パック構成（ディレクトリ設計）

`qa4aidd-gate-coach/
├── packages/                          # 工程パック
│   ├── PLN/                           # 企画パック
│   │   ├── checklists/
│   │   │   ├── CHK-PLN-CONSIST-001.yaml   # MD↔YAML整合性
│   │   │   └── CHK-PLN-SCOPE-001.yaml     # スコープ検証可能性
│   │   ├── schemas/
│   │   │   └── planning.schema.json
│   │   ├── prompts/
│   │   │   └── ambiguitycheck.yaml
│   │   └── pack.yaml                  # パックメタ情報
│   │
│   ├── REQ/                           # 要件定義パック
│   │   ├── checklists/
│   │   │   ├── CHK-REQ-REVIEW-001.yaml    # 要件妥当性（提供済み）
│   │   │   ├── CHK-REQ-TRACE-001.yaml     # トレーサビリティ
│   │   │   └── CHK-REQ-AI-001.yaml        # AI可読性
│   │   ├── schemas/
│   │   │   └── requirements.schema.json
│   │   ├── prompts/
│   │   │   ├── verifiability.yaml
│   │   │   └── deepevalcriteria.yaml
│   │   └── pack.yaml
│   │
│   ├── BAS/                           # 基本設計パック
│   │   └── ...
│   │
│   └── DET/                           # 詳細設計パック
│       └── ...
│
├── coach-ui/                          # フロントエンド
│   ├── src/
│   │   ├── components/
│   │   │   ├── PhaseTab.tsx
│   │   │   ├── ChecklistItem.tsx
│   │   │   ├── DetailPanel.tsx
│   │   │   └── StatusButton.tsx
│   │   ├── hooks/
│   │   │   └── useChecklistState.ts
│   │   └── utils/
│   │       └── jsonExporter.ts
│   └── package.json
│
├── gate-runner/                       # バックエンド/CLI
│   ├── gates/
│   │   ├── g1ambiguity.py
│   │   ├── g2checklistvalidator.py  # ★ ④の実現
│   │   ├── g3schema.py
│   │   ├── g4deepeval.py
│   │   └── g5traceability.py
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── allure-config/                     # Allure設定
│   └── categories.json
│
└── examples/                          # サンプルプロジェクト
    └── sample-project/
        ├── planning.yaml
        ├── requirements.yaml
        └── checklistoutput.json`

④の実現可能性（再評価）
結論：十分実現可能（複雑ではない）

`┌─────────────────────────────────────────────────────────────────┐
│                        実現アプローチ                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Coach UI                                                      │
│      │                                                          │
│      │ JSON出力（checklistresults.json）                       │
│      ▼                                                          │
│   ┌─────────────────────────────────────────┐                   │
│   │  Git リポジトリにコミット               │                   │
│   │  artifacts/checklistresults.json       │                   │
│   └─────────────────────────────────────────┘                   │
│      │                                                          │
│      │ Push / PR                                                │
│      ▼                                                          │
│   ┌─────────────────────────────────────────┐                   │
│   │  CI/CD Pipeline (GitHub Actions等)      │                   │
│   │                                         │                   │
│   │  Step 1: Docker Pull qa4aidd-gate       │                   │
│   │  Step 2: Mount artifacts → Run G2       │                   │
│   │  Step 3: G2がchecklist.jsonを検証       │                   │
│   │          ├─ 全項目Done/Abort? → OK      │                   │
│   │          ├─ Abort理由あり? → OK         │                   │
│   │          └─ Todoが残存? → FAIL          │                   │
│   │  Step 4: exit code で Build Pass/Fail   │                   │
│   └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘`

必要な実装（最小構成）

| コンポーネント        | 工数目安 | 難易度 |
| --------------------- | -------- | ------ |
| G2 Validator (Python) | 2-3日    | ★★☆☆☆  |
| JSON Schema定義       | 1日      | ★☆☆☆☆  |
| GitHub Actions設定    | 0.5日    | ★☆☆☆☆  |
| Docker イメージ化     | 1日      | ★★☆☆☆  |

→ 最短1週間で④は実現可能

ConTrack連携設計（Adapter層）

`┌──────────────────────────────────────────────────────────────┐
│                     Traceability 2層設計                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Core Layer（本ツール）                                │  │
│  │  ・ID抽出（PLN-xxx, REQ-xxx, BAS-xxx...）              │  │
│  │  ・参照整合チェック（derivedFrom存在確認）             │  │
│  │  ・カバレッジ算出（未紐付け一覧）                      │  │
│  │  ・Allure出力（trace_matrix）                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                             │                                │
│                             ▼                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Adapter Layer（将来拡張）                             │  │
│  │  ・ConTrack API連携                                    │  │
│  │    - 存在確認: GET /items/{id}                         │  │
│  │    - リンク生成: POST /links                           │  │
│  │    - 参照先解決: GET /items/{id}/relations             │  │
│  │  ・他ツール連携（Jira, Notion等）も同じ構造で拡張可    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘`

導入ロードマップ（社内展開）

`
Phase 1 Phase 2 Phase 3
(1ヶ月) (2ヶ月) (3ヶ月〜)
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ REQパック配布 │ → │ PLNパック追加 │ → │ BAS/DET拡張 │
│ │ │ │ │ │
│ ・Coach UIの │ │ ・企画段階から│ │ ・フル工程 │
│ み先行配布 │ │ 品質観点導入│ │ カバレッジ │
│ ・視座共有を │ │ ・MD↔YAML │ │ ・ConTrack │
│ 優先 │ │ 整合性ゲート│ │ Adapter実装 │
│ │ │ │ │ │
│ ・Runner任意 │ │ ・CI組込み │ │ ・組織展開 │
│ （ローカル）│ │ 推奨 │ │ │
└───────────────┘ └───────────────┘ └───────────────┘
│ │ │
▼ ▼ ▼
成功指標: 成功指標: 成功指標:
・利用者10名以上 ・企画起点の ・手戻り30%削減
・「迷わない」 　品質議論が発生 ・Allureで品質
フィードバック ・CI組込み3チーム 説明可能
``

成功条件（KPI）

| 指標                 | Phase 1  | Phase 2 | Phase 3  |
| -------------------- | -------- | ------- | -------- |
| Coach UI利用者数     | 10名+    | 30名+   | 全対象者 |
| チェックリスト完了率 | 70%+     | 85%+    | 95%+     |
| Done/Abort理由記入率 | 100%     | 100%    | 100%     |
| CI組込みチーム数     | 1+       | 3+      | 全チーム |
| 手戻り削減率         | 計測開始 | 15%+    | 30%+     |

主な改善点まとめ

| 項目         | 元企画             | 改善後                                 |
| ------------ | ------------------ | -------------------------------------- |
| ④の実現性    | 「困難な気がする」 | G2 Validator設計で実現可能と明示       |
| Coach UI     | 概念のみ           | 画面フロー・状態遷移・JSON仕様を具体化 |
| ディレクトリ | 未定義             | 工程パック構成を明示                   |
| CI連携       | 任意               | GitHub Actions例を追加                 |
| ConTrack     | 方針のみ           | 2層設計（Core/Adapter）を具体化        |
| ロードマップ | 段階導入           | Phase別KPI付きで明確化                 |
