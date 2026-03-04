"use client";

import { ExportButton } from "@/components/coach/ExportButton";
import { NodeCard } from "@/components/coach/NodeCard";
import { NodeDetailPanel } from "@/components/coach/NodeDetailPanel";
import { useSession } from "@/context/SessionContext";
import { planningChecklist, planningPhase } from "@/data/planningChecklist";
import { usePlanningPhaseRun } from "@/hooks/usePlanningPhaseRun";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

export default function PhasePlanningPage() {
  const router = useRouter();
  const { session, isReady: isSessionReady } = useSession();
  const { run, isReady: isRunReady, visibleNodes, updateNodeFields, setNodeStatus, exportRun } = usePlanningPhaseRun(session);

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  useEffect(() => {
    if (isSessionReady && !session) {
      router.replace("/login");
    }
  }, [isSessionReady, session, router]);

  const effectiveSelectedNodeId = useMemo(() => {
    if (selectedNodeId && visibleNodes.some((node) => node.id === selectedNodeId)) {
      return selectedNodeId;
    }
    return visibleNodes[0]?.id ?? null;
  }, [selectedNodeId, visibleNodes]);

  const selectedNode = useMemo(
    () => planningChecklist.find((node) => node.id === effectiveSelectedNodeId) ?? null,
    [effectiveSelectedNodeId]
  );
  const selectedResult = effectiveSelectedNodeId && run ? run.results[effectiveSelectedNodeId] ?? null : null;
  const lockedCount = planningChecklist.length - visibleNodes.length;

  if (!isSessionReady || !session || !isRunReady || !run) {
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
        background: "linear-gradient(170deg, #f8fbff, #f1f5f9)",
        color: "#0f172a",
        padding: "70px 20px 40px",
      }}
    >
      <ExportButton onExport={exportRun} disabled={!run} />

      <section
        style={{
          maxWidth: 860,
          margin: "0 auto",
          display: "grid",
          gap: 16,
        }}
      >
        <header style={{ display: "grid", gap: 8 }}>
          <button
            type="button"
            onClick={() => router.push("/")}
            style={{
              justifySelf: "start",
              border: "1px solid #cbd5e1",
              borderRadius: 10,
              padding: "8px 10px",
              background: "#ffffff",
              cursor: "pointer",
            }}
          >
            Topへ戻る
          </button>
          <h1 style={{ margin: 0, fontSize: 30 }}>{planningPhase.name} フェーズ</h1>
          <p style={{ margin: 0, color: "#334155" }}>{planningPhase.description}</p>
          <p style={{ margin: 0, fontSize: 13, color: "#64748b" }}>
            実行者: {run.user.username} ({run.user.role}) / ログ件数: {run.logs.length}
          </p>
        </header>

        <section
          style={{
            border: "1px solid #d8dee7",
            borderRadius: 16,
            background: "#ffffff",
            padding: "16px 14px",
            display: "grid",
            gap: 12,
          }}
        >
          <h2 style={{ margin: "0 0 4px", fontSize: 20 }}>ノード一覧</h2>
          {visibleNodes.map((node) => (
            <NodeCard
              key={node.id}
              node={node}
              result={run.results[node.id] ?? null}
              isActive={node.id === effectiveSelectedNodeId}
              onClick={() => {
                setSelectedNodeId(node.id);
                setIsPanelOpen(true);
              }}
            />
          ))}
          <p style={{ margin: "4px 0 0", fontSize: 13, color: "#64748b" }}>未解放ノード: {lockedCount}</p>
        </section>
      </section>

      <NodeDetailPanel
        isOpen={isPanelOpen && Boolean(effectiveSelectedNodeId)}
        node={selectedNode}
        result={selectedResult}
        onClose={() => setIsPanelOpen(false)}
        onUpdateFields={updateNodeFields}
        onStatusChange={setNodeStatus}
      />
    </main>
  );
}
