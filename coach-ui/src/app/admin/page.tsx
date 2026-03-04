"use client";

import { useSession } from "@/context/SessionContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function AdminPage() {
  const router = useRouter();
  const { session, isReady } = useSession();

  useEffect(() => {
    if (!isReady) {
      return;
    }
    if (!session) {
      router.replace("/login");
      return;
    }
    if (session.role !== "Admin") {
      router.replace("/");
    }
  }, [isReady, session, router]);

  if (!isReady || !session || session.role !== "Admin") {
    return (
      <main style={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
        <p>Loading...</p>
      </main>
    );
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "linear-gradient(160deg, #f8fbff, #eef4fb)",
        padding: "56px 20px",
      }}
    >
      <section
        style={{
          maxWidth: 860,
          margin: "0 auto",
          border: "1px solid #d8dee7",
          borderRadius: 16,
          background: "#ffffff",
          padding: "24px 22px",
          display: "grid",
          gap: 12,
        }}
      >
        <h1 style={{ margin: 0 }}>管理者ダッシュボード（MVP stub）</h1>
        <p style={{ margin: 0, color: "#475569" }}>管理画面は次段で実装します。現時点では見出しのみ提供しています。</p>
        <h2 style={{ marginBottom: 0 }}>ユーザー一覧</h2>
        <p style={{ marginTop: 0, color: "#64748b" }}>未実装</p>
        <h2 style={{ marginBottom: 0 }}>ロール変更</h2>
        <p style={{ marginTop: 0, color: "#64748b" }}>未実装</p>
        <h2 style={{ marginBottom: 0 }}>ログ閲覧</h2>
        <p style={{ marginTop: 0, color: "#64748b" }}>未実装</p>

        <button
          type="button"
          onClick={() => router.push("/")}
          style={{
            justifySelf: "start",
            border: "1px solid #cbd5e1",
            borderRadius: 10,
            padding: "8px 12px",
            background: "#f8fafc",
            cursor: "pointer",
          }}
        >
          Topへ戻る
        </button>
      </section>
    </main>
  );
}
