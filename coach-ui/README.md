# coach-ui

品質ゲート基盤の Coach UI MVP（Next.js + TypeScript）です。
ローカル完結（擬似認証 + localStorage 保存）で、企画フェーズのチェック進行と JSON エクスポートを行います。

## 起動

```bash
npm install
npm run dev
```

ブラウザで `http://localhost:3000` を開きます。

## ログイン方法（MVP）

- `admin / admin` で `Admin`
- 上記以外は `User`

ログイン状態は `localStorage` の `coach.session` に保存されます。

## 画面構成

- `/login`
  - 擬似ログイン画面
- `/`
  - Top 画面（Getting Started）
  - Admin のみ「管理者ダッシュボード」ボタン表示
- `/phase/planning`
  - 企画フェーズ画面
  - ノードを順に解放
  - 右サイドパネルで詳細確認・ステータス変更
  - 左上固定の JSON エクスポート
- `/admin`
  - Admin のみアクセス可（MVP stub）

## 操作フロー（MVP）

1. `/login` でログイン
2. `/` で `Getting Started` を押下
3. `/phase/planning` で先頭ノードから確認
4. ノードをクリックしてサイドパネルを開く
5. `checkedBy` を入力してステータス変更
   - `Pending` は理由入力が必須
6. `Done` または `Pending(理由あり)` で次ノードが解放
7. 左上の `JSONエクスポート` から結果をダウンロード

## 保存キー

- セッション: `coach.session`
- 企画フェーズ実行データ: `coach.phase.planning`

## 出力 JSON

- ファイル名: `checklistresults_planning_<YYYYMMDD_HHMM>.json`
- `PhaseRun` 相当の実行結果 + ステータス変更ログを含みます
