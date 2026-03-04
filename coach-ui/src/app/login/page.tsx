"use client";

import { useSession } from "@/context/SessionContext";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

export default function LoginPage() {
  const router = useRouter();
  const { session, isReady, login } = useSession();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (isReady && session) {
      router.replace("/");
    }
  }, [isReady, session, router]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedName = username.trim();
    if (!normalizedName || !password) {
      setErrorMessage("ユーザー名とパスワードを入力してください。");
      return;
    }

    login(normalizedName, password);
    router.replace("/");
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        background: "linear-gradient(135deg, #f8fbff, #edf3ff)",
        padding: 20,
      }}
    >
      <section
        style={{
          width: "min(460px, 100%)",
          border: "1px solid #d8dee7",
          borderRadius: 16,
          padding: "28px 24px",
          background: "#ffffff",
          boxShadow: "0 14px 32px rgba(15, 23, 42, 0.08)",
        }}
      >
        <h1 style={{ margin: "0 0 10px", fontSize: 28 }}>Coach UI Login</h1>
        <p style={{ margin: "0 0 18px", color: "#475569", lineHeight: 1.6 }}>
          MVP では擬似認証です。`admin / admin` で Admin、それ以外は User としてログインします。
        </p>

        <form onSubmit={handleSubmit} style={{ display: "grid", gap: 14 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontWeight: 600 }}>ユーザー名 or メール</span>
            <input
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 10,
                padding: "10px 12px",
              }}
            />
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontWeight: 600 }}>パスワード</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 10,
                padding: "10px 12px",
              }}
            />
          </label>

          {errorMessage ? (
            <p
              style={{
                margin: 0,
                border: "1px solid #fecaca",
                background: "#fef2f2",
                color: "#b91c1c",
                borderRadius: 10,
                padding: "8px 10px",
              }}
            >
              {errorMessage}
            </p>
          ) : null}

          <button
            type="submit"
            style={{
              border: "1px solid #12324f",
              borderRadius: 10,
              padding: "10px 14px",
              background: "#12324f",
              color: "#ffffff",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            ログイン
          </button>
        </form>
      </section>
    </main>
  );
}
