"use client";

import { SessionProvider } from "@/context/SessionContext";
import { ReactNode } from "react";

export default function AppProviders({ children }: { children: ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>;
}
