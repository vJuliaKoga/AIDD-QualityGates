"use client";

import { useSession } from "@/context/SessionContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function TopPage() {
  const router = useRouter();
  const { session, isReady, logout } = useSession();

  useEffect(() => {
    if (isReady && !session) {
      router.replace("/login");
    }
  }, [isReady, session, router]);

  if (!isReady || !session) {
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
        color: "#0f172a",
        padding: "64px 20px 40px",
      }}
    >
      <section
        style={{
          maxWidth: 840,
          margin: "0 auto",
          border: "1px solid #d8dee7",
          borderRadius: 16,
          background: "#ffffff",
          padding: "28px 24px",
          display: "grid",
          gap: 18,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "start", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ margin: "0 0 8px", fontSize: 30 }}>QualityGate Coach UI</h1>
            <p style={{ margin: 0, color: "#334155", lineHeight: 1.6 }}>
              品質ゲートのチェック項目を順に進め、確認記録を残して JSON でエクスポートできる MVP です。
            </p>
          </div>
          <div style={{ textAlign: "right", minWidth: 160 }}>
            <p style={{ margin: "0 0 8px", fontSize: 13, color: "#475569" }}>
              {session.username} ({session.role})
            </p>
            <button
              type="button"
              onClick={() => {
                logout();
                router.replace("/login");
              }}
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 10,
                padding: "8px 12px",
                background: "#f8fafc",
                cursor: "pointer",
              }}
            >
              ログアウト
            </button>
          </div>
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={() => router.push("/phase/planning")}
            style={{
              border: "1px solid #12324f",
              borderRadius: 12,
              padding: "10px 14px",
              background: "#12324f",
              color: "#ffffff",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            Getting Started
          </button>

          {session.role === "Admin" ? (
            <button
              type="button"
              onClick={() => router.push("/admin")}
              style={{
                border: "1px solid #1d4ed8",
                borderRadius: 12,
                padding: "10px 14px",
                background: "#eff6ff",
                color: "#1e3a8a",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              管理者ダッシュボード
            </button>
          ) : null}
        </div>
      </section>
    </main>
  );
}
