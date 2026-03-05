// ============================================================
// CheckFlow API Server (Phase 1 MVP)
// ============================================================
// 起動: npm start  (http://localhost:3001)
// リセット: npm run reset → npm start
// ============================================================

const express = require('express');
const cors = require('cors');
const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 3001;

// --- Middleware ---
app.use(cors());
app.use(express.json());

// --- DB Setup ---
const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });

const dbPath = path.join(dataDir, 'checkflow.db');
const db = new Database(dbPath);

// WALモードで高速化 + 同時アクセス安全性
db.pragma('journal_mode = WAL');

// テーブル作成
db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password    TEXT    NOT NULL,
    role        TEXT    NOT NULL DEFAULT 'User' CHECK(role IN ('Admin', 'User')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
  );
`);

// 初期Adminユーザー（テーブルが空のときだけ挿入）
const userCount = db.prepare('SELECT COUNT(*) AS cnt FROM users').get();
if (userCount.cnt === 0) {
  db.prepare('INSERT INTO users (username, password, role) VALUES (?, ?, ?)').run('Sam', 'admin', 'Admin');
  console.log('[INIT] Default admin user created: Sam / admin');
}

// --- Prepared Statements (高速化) ---
const stmts = {
  findUser:     db.prepare('SELECT id, username, password, role, created_at FROM users WHERE username = ? COLLATE NOCASE'),
  allUsers:     db.prepare('SELECT id, username, role, created_at FROM users ORDER BY id'),
  insertUser:   db.prepare('INSERT INTO users (username, password, role) VALUES (?, ?, ?)'),
  updateRole:   db.prepare('UPDATE users SET role = ? WHERE username = ? COLLATE NOCASE'),
  deleteUser:   db.prepare('DELETE FROM users WHERE username = ? COLLATE NOCASE'),
};

// ============================================================
// API Endpoints
// ============================================================

// POST /api/login — ログイン認証
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  if (!username?.trim() || !password?.trim()) {
    return res.status(400).json({ error: 'ユーザー名とパスワードを入力してください。' });
  }
  const user = stmts.findUser.get(username.trim());
  if (!user) {
    return res.status(401).json({ error: 'ユーザーが見つかりません。管理者にアカウント作成を依頼してください。' });
  }
  if (user.password !== password) {
    return res.status(401).json({ error: 'パスワードが正しくありません。' });
  }
  // パスワードは返さない
  res.json({ username: user.username, role: user.role });
});

// GET /api/users — ユーザー一覧（管理用）
app.get('/api/users', (req, res) => {
  const users = stmts.allUsers.all();
  res.json(users);
});

// POST /api/users — ユーザー作成（Admin専用）
app.post('/api/users', (req, res) => {
  const { username, password, role } = req.body;
  if (!username?.trim()) {
    return res.status(400).json({ error: 'ユーザー名を入力してください。' });
  }
  if (username.trim().length > 30) {
    return res.status(400).json({ error: '30文字以内で入力してください。' });
  }
  if (!password?.trim()) {
    return res.status(400).json({ error: '初期パスワードを設定してください。' });
  }
  if (password.trim().length < 3) {
    return res.status(400).json({ error: 'パスワードは3文字以上にしてください。' });
  }
  const validRole = role === 'Admin' ? 'Admin' : 'User';

  try {
    stmts.insertUser.run(username.trim(), password.trim(), validRole);
    res.json({ message: `「${username.trim()}」を ${validRole} として登録しました。` });
  } catch (err) {
    if (err.message.includes('UNIQUE')) {
      return res.status(409).json({ error: 'このユーザー名は既に登録されています。' });
    }
    return res.status(500).json({ error: 'ユーザー作成に失敗しました。' });
  }
});

// PUT /api/users/:name/role — ロール変更（Admin専用）
app.put('/api/users/:name/role', (req, res) => {
  const { name } = req.params;
  const { role, requestedBy } = req.body;
  if (!role || !['Admin', 'User'].includes(role)) {
    return res.status(400).json({ error: '有効なロールを指定してください。' });
  }
  // 自分自身のUser降格を防止
  if (requestedBy && requestedBy.toLowerCase() === name.toLowerCase() && role === 'User') {
    return res.status(400).json({ error: '自分自身をUserに降格できません。' });
  }
  const user = stmts.findUser.get(name);
  if (!user) {
    return res.status(404).json({ error: 'ユーザーが見つかりません。' });
  }
  stmts.updateRole.run(role, name);
  res.json({ message: `「${name}」のロールを ${role} に変更しました。` });
});

// DELETE /api/users/:name — ユーザー削除（Admin専用）
app.delete('/api/users/:name', (req, res) => {
  const { name } = req.params;
  const requestedBy = req.query.requestedBy || '';
  // 自分自身の削除を防止
  if (requestedBy.toLowerCase() === name.toLowerCase()) {
    return res.status(400).json({ error: '自分自身は削除できません。' });
  }
  const user = stmts.findUser.get(name);
  if (!user) {
    return res.status(404).json({ error: 'ユーザーが見つかりません。' });
  }
  stmts.deleteUser.run(name);
  res.json({ message: `「${name}」を削除しました。` });
});

// --- Health check ---
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', users: db.prepare('SELECT COUNT(*) AS cnt FROM users').get().cnt });
});

// --- Start ---
app.listen(PORT, () => {
  console.log(`\n✅ CheckFlow API Server running on http://localhost:${PORT}`);
  console.log(`   Health check: http://localhost:${PORT}/api/health`);
  console.log(`   DB location:  ${dbPath}\n`);
});

// --- Graceful shutdown ---
process.on('SIGINT', () => { db.close(); process.exit(0); });
process.on('SIGTERM', () => { db.close(); process.exit(0); });
