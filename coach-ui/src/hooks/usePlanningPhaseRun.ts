"use client";

import { planningChecklist, planningPhase } from "@/data/planningChecklist";
import { loadPlanningPhaseRun, savePlanningPhaseRun } from "@/lib/coachStorage";
import { CoachSession, NodeResult, NodeStatus, PhaseRun, StatusChangeLog } from "@/lib/coachTypes";
import { useCallback, useEffect, useMemo, useState } from "react";

type NodeFieldPatch = {
  checkedBy?: string;
  reason?: string;
};

type StatusUpdateResult =
  | {
      ok: true;
    }
  | {
      ok: false;
      error: string;
    };

const nowIso = () => new Date().toISOString();

function createEmptyNodeResult(nodeId: string): NodeResult {
  return {
    nodeId,
    status: "ToDo",
    checkedBy: "",
    updatedAt: nowIso(),
  };
}

function createPhaseRun(session: CoachSession): PhaseRun {
  const timestamp = nowIso();
  return {
    phaseId: planningPhase.id,
    sessionId: session.sessionId,
    user: {
      username: session.username,
      role: session.role,
    },
    startedAt: timestamp,
    updatedAt: timestamp,
    results: {},
    logs: [],
  };
}

function canUnlockByResult(result: NodeResult | undefined) {
  if (!result) {
    return false;
  }
  if (result.status === "Done") {
    return true;
  }
  if (result.status === "Pending") {
    return Boolean(result.reason?.trim());
  }
  return false;
}

function formatDateForFileName(date: Date) {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  const hh = String(date.getHours()).padStart(2, "0");
  const min = String(date.getMinutes()).padStart(2, "0");
  return `${yyyy}${mm}${dd}_${hh}${min}`;
}

function normalizeReason(value: string | undefined) {
  if (!value || !value.trim()) {
    return undefined;
  }
  return value;
}

function buildStatusLog(args: {
  nodeId: string;
  from: NodeStatus;
  to: NodeStatus;
  checkedBy: string;
  reason?: string;
  updatedAt: string;
}): StatusChangeLog {
  return {
    id: `${args.nodeId}_${Date.now()}`,
    nodeId: args.nodeId,
    from: args.from,
    to: args.to,
    checkedBy: args.checkedBy,
    updatedAt: args.updatedAt,
    ...(args.reason ? { reason: args.reason } : {}),
  };
}

export function usePlanningPhaseRun(session: CoachSession | null) {
  const [run, setRun] = useState<PhaseRun | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (!session) {
      const clearTimer = window.setTimeout(() => {
        setRun(null);
        setIsReady(true);
      }, 0);
      return () => window.clearTimeout(clearTimer);
    }

    const hydrateTimer = window.setTimeout(() => {
      const storedRun = loadPlanningPhaseRun();
      if (storedRun) {
        setRun({
          ...storedRun,
          sessionId: session.sessionId,
          user: {
            username: session.username,
            role: session.role,
          },
          logs: storedRun.logs ?? [],
        });
      } else {
        setRun(createPhaseRun(session));
      }

      setIsReady(true);
    }, 0);

    return () => window.clearTimeout(hydrateTimer);
  }, [session]);

  useEffect(() => {
    if (!run) {
      return;
    }
    savePlanningPhaseRun(run);
  }, [run]);

  const unlockedNodeIds = useMemo(() => {
    const unlocked = new Set<string>();
    const firstNode = planningChecklist[0];
    if (!firstNode) {
      return unlocked;
    }

    unlocked.add(firstNode.id);
    let changed = true;

    while (changed) {
      changed = false;
      for (const node of planningChecklist) {
        if (!unlocked.has(node.id)) {
          continue;
        }
        const result = run?.results[node.id];
        if (!canUnlockByResult(result)) {
          continue;
        }

        for (const nextNodeId of node.unlocks ?? []) {
          if (!unlocked.has(nextNodeId)) {
            unlocked.add(nextNodeId);
            changed = true;
          }
        }
      }
    }

    return unlocked;
  }, [run]);

  const visibleNodes = useMemo(
    () => planningChecklist.filter((node) => unlockedNodeIds.has(node.id)),
    [unlockedNodeIds]
  );

  const updateNodeFields = useCallback((nodeId: string, patch: NodeFieldPatch) => {
    setRun((currentRun) => {
      if (!currentRun) {
        return currentRun;
      }

      const currentResult = currentRun.results[nodeId] ?? createEmptyNodeResult(nodeId);
      const checkedBy = patch.checkedBy ?? currentResult.checkedBy;
      const reasonInput = patch.reason !== undefined ? patch.reason : currentResult.reason;
      const reason = normalizeReason(reasonInput);
      const updatedAt = nowIso();

      const nextResult: NodeResult = {
        nodeId,
        status: currentResult.status,
        checkedBy,
        updatedAt,
        ...(reason ? { reason } : {}),
      };

      return {
        ...currentRun,
        updatedAt,
        results: {
          ...currentRun.results,
          [nodeId]: nextResult,
        },
      };
    });
  }, []);

  const setNodeStatus = useCallback(
    (nodeId: string, nextStatus: NodeStatus): StatusUpdateResult => {
      if (!run) {
        return { ok: false, error: "フェーズデータの読み込み中です。" };
      }

      const currentResult = run.results[nodeId] ?? createEmptyNodeResult(nodeId);
      const checkedBy = currentResult.checkedBy.trim();
      const reason = normalizeReason(currentResult.reason);

      if (!checkedBy) {
        return { ok: false, error: "確認者名を入力してください。" };
      }
      if (nextStatus === "Pending" && !reason) {
        return { ok: false, error: "Pending を選ぶ場合は理由を入力してください。" };
      }

      const updatedAt = nowIso();
      setRun((currentRun) => {
        if (!currentRun) {
          return currentRun;
        }

        const latestResult = currentRun.results[nodeId] ?? createEmptyNodeResult(nodeId);
        const latestReason = normalizeReason(latestResult.reason);
        const nextResult: NodeResult = {
          nodeId,
          status: nextStatus,
          checkedBy: latestResult.checkedBy,
          updatedAt,
          ...(latestReason ? { reason: latestReason } : {}),
        };

        const log = buildStatusLog({
          nodeId,
          from: latestResult.status,
          to: nextStatus,
          checkedBy: latestResult.checkedBy,
          reason: latestReason,
          updatedAt,
        });

        return {
          ...currentRun,
          updatedAt,
          results: {
            ...currentRun.results,
            [nodeId]: nextResult,
          },
          logs: [...(currentRun.logs ?? []), log],
        };
      });

      return { ok: true };
    },
    [run]
  );

  const exportRun = useCallback(() => {
    if (!run) {
      return;
    }
    const exportedAt = nowIso();
    const fileName = `checklistresults_planning_${formatDateForFileName(new Date())}.json`;
    const payload = {
      ...run,
      exportedAt,
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = fileName;
    anchor.click();
    URL.revokeObjectURL(url);
  }, [run]);

  return {
    run,
    isReady,
    unlockedNodeIds,
    visibleNodes,
    updateNodeFields,
    setNodeStatus,
    exportRun,
  };
}
