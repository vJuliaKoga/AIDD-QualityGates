# CheckFlow API Server セットアップ

## 初回セットアップ

```bash
cd server
npm install
npm start
```

起動すると以下が表示されます：
```
✅ CheckFlow API Server running on http://localhost:3001
   Health check: http://localhost:3001/api/health
   DB location:  server/data/checkflow.db
```

初回起動時、管理者アカウントが自動作成されます：
- **Username:** Sam
- **Password:** admin
- **Role:** Admin

**管理者アカウントを変更したい場合**

手段①：tools\checklist\CheckFlow\server\index.jsのSamをRename
手段②：初回だけSamで入りアカウント作成→Samを削除

## フロントエンドの起動（別ターミナル）

```bash
cd CheckFlow
npm run dev
```

## DBリセット（配布前・初期化したいとき）

```bash
cd server
npm run reset     # DBファイルを削除
npm start         # 再起動で初期Admin再作成
```

## 配布時の注意

- `server/data/checkflow.db` は `.gitignore` 済み
- 受け取った人は `npm install` → `npm start` で新品DBが自動生成される
- ユーザーデータは各環境のDBファイルに保存される

## API エンドポイント一覧

| Method | Path | 用途 |
|--------|------|------|
| GET | `/api/health` | サーバー稼働確認 |
| POST | `/api/login` | ログイン認証 |
| GET | `/api/users` | ユーザー一覧取得 |
| POST | `/api/users` | ユーザー作成（Admin専用） |
| PUT | `/api/users/:name/role` | ロール変更（Admin専用） |
| DELETE | `/api/users/:name` | ユーザー削除（Admin専用） |

