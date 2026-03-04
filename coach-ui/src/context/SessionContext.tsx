"use client";

import { clearSession, loadSession, saveSession } from "@/lib/coachStorage";
import { CoachSession, UserRole } from "@/lib/coachTypes";
import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";

type SessionContextValue = {
  session: CoachSession | null;
  isReady: boolean;
  login: (username: string, password: string) => CoachSession;
  logout: () => void;
};

const SessionContext = createContext<SessionContextValue | null>(null);

const nowIso = () => new Date().toISOString();

function createSession(username: string, role: UserRole): CoachSession {
  const sessionId =
    typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `session_${Date.now()}`;

  return {
    username,
    role,
    sessionId,
    loggedInAt: nowIso(),
  };
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<CoachSession | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSession(loadSession());
      setIsReady(true);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const login = useCallback((username: string, password: string) => {
    const normalizedName = username.trim();
    const nextRole: UserRole = normalizedName === "admin" && password === "admin" ? "Admin" : "User";
    const nextSession = createSession(normalizedName || "guest", nextRole);
    saveSession(nextSession);
    setSession(nextSession);
    return nextSession;
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setSession(null);
  }, []);

  const value = useMemo(
    () => ({
      session,
      isReady,
      login,
      logout,
    }),
    [session, isReady, login, logout]
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used within SessionProvider.");
  }
  return context;
}
