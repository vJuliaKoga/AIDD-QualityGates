"use client";

import { ChecklistNode, NodeResult, NodeStatus } from "@/lib/coachTypes";
import { useMemo } from "react";

type NodeDetailPanelProps = {
  isOpen: boolean;
  node: ChecklistNode | null;
  result: NodeResult | null;
  onClose: () => void;
  onUpdateFields: (nodeId: string, patch: { checkedBy?: string; reason?: string }) => void;
  onStatusChange: (nodeId: string, status: NodeStatus) => { ok: boolean; error?: string };
};

const statuses: NodeStatus[] = ["ToDo", "InProgress", "Pending", "Done"];

export function NodeDetailPanel({
  isOpen,
  node,
  result,
  onClose,
  onUpdateFields,
  onStatusChange,
}: NodeDetailPanelProps) {
  const checkedBy = result?.checkedBy ?? "";
  const reason = result?.reason ?? "";

  const canChangeAnyStatus = useMemo(() => Boolean(checkedBy.trim()), [checkedBy]);
  const canSetPending = useMemo(() => canChangeAnyStatus && Boolean(reason.trim()), [canChangeAnyStatus, reason]);

  if (!isOpen || !node) {
    return null;
  }
  const nodeId = node.id;

  function handleStatusChange(status: NodeStatus) {
    const outcome = onStatusChange(nodeId, status);
    if (!outcome.ok) {
      window.alert(outcome.error ?? "ステータス変更に失敗しました。");
      return;
    }
  }

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(15, 23, 42, 0.35)",
        zIndex: 20,
        display: "flex",
        justifyContent: "flex-end",
      }}
    >
      <aside
        onClick={(event) => event.stopPropagation()}
        style={{
          width: "min(460px, 92vw)",
          height: "100%",
          background: "#ffffff",
          borderLeft: "1px solid #d8dee7",
          padding: 20,
          overflowY: "auto",
          boxShadow: "-8px 0 24px rgba(15, 23, 42, 0.12)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center" }}>
          <h2 style={{ margin: 0, fontSize: 22 }}>{node.title}</h2>
          <button
            type="button"
            onClick={onClose}
            style={{
              border: "1px solid #d8dee7",
              background: "#f8fafc",
              borderRadius: 8,
              padding: "6px 10px",
              cursor: "pointer",
            }}
          >
            閉じる
          </button>
        </div>

        {node.description ? <p style={{ color: "#334155" }}>{node.description}</p> : null}

        <section style={{ display: "grid", gap: 8 }}>
          <h3 style={{ margin: "8px 0 0", fontSize: 16 }}>ステータス</h3>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {statuses.map((status) => {
              const disabled = status === "Pending" ? !canSetPending : !canChangeAnyStatus;
              const isActive = result?.status === status;
              return (
                <button
                  key={status}
                  type="button"
                  onClick={() => handleStatusChange(status)}
                  disabled={disabled}
                  style={{
                    borderRadius: 10,
                    border: isActive ? "1px solid #12324f" : "1px solid #cbd5e1",
                    padding: "8px 10px",
                    background: isActive ? "#12324f" : "#ffffff",
                    color: isActive ? "#ffffff" : "#1e293b",
                    cursor: disabled ? "not-allowed" : "pointer",
                    opacity: disabled ? 0.45 : 1,
                    fontWeight: 600,
                  }}
                >
                  {status}
                </button>
              );
            })}
          </div>
          {!canChangeAnyStatus ? (
            <p style={{ margin: 0, color: "#b45309", fontSize: 13 }}>確認者名を入力するとステータス変更できます。</p>
          ) : null}
          {canChangeAnyStatus && !canSetPending ? (
            <p style={{ margin: 0, color: "#b45309", fontSize: 13 }}>Pending を選ぶには理由入力が必要です。</p>
          ) : null}
        </section>

        <section style={{ marginTop: 16, display: "grid", gap: 12 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontWeight: 600 }}>確認者名（必須）</span>
            <input
              type="text"
              value={checkedBy}
              onChange={(event) => onUpdateFields(nodeId, { checkedBy: event.target.value })}
              placeholder="例: yamada"
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 10,
                padding: "10px 12px",
              }}
            />
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontWeight: 600 }}>理由（Pending 時は必須）</span>
            <textarea
              value={reason}
              onChange={(event) => onUpdateFields(nodeId, { reason: event.target.value })}
              placeholder="Pending にする理由を入力"
              rows={4}
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 10,
                padding: "10px 12px",
                resize: "vertical",
              }}
            />
          </label>
        </section>

        <section style={{ marginTop: 20, display: "grid", gap: 12 }}>
          <h3 style={{ margin: 0, fontSize: 16 }}>PASS / FAIL / ABORT 例</h3>

          <div>
            <p style={{ margin: "0 0 6px", fontWeight: 600 }}>PASS</p>
            {node.examples?.pass?.length ? (
              <ul style={{ margin: 0, paddingLeft: 18, color: "#334155" }}>
                {node.examples.pass.map((text) => (
                  <li key={text}>{text}</li>
                ))}
              </ul>
            ) : (
              <p style={{ margin: 0, color: "#64748b" }}>未定義</p>
            )}
          </div>

          <div>
            <p style={{ margin: "0 0 6px", fontWeight: 600 }}>FAIL</p>
            {node.examples?.fail?.length ? (
              <ul style={{ margin: 0, paddingLeft: 18, color: "#334155" }}>
                {node.examples.fail.map((text) => (
                  <li key={text}>{text}</li>
                ))}
              </ul>
            ) : (
              <p style={{ margin: 0, color: "#64748b" }}>未定義</p>
            )}
          </div>

          <div>
            <p style={{ margin: "0 0 6px", fontWeight: 600 }}>ABORT</p>
            {node.examples?.abort?.length ? (
              <ul style={{ margin: 0, paddingLeft: 18, color: "#334155" }}>
                {node.examples.abort.map((text) => (
                  <li key={text}>{text}</li>
                ))}
              </ul>
            ) : (
              <p style={{ margin: 0, color: "#64748b" }}>未定義</p>
            )}
          </div>
        </section>

        <p style={{ marginTop: 18, fontSize: 12, color: "#64748b" }}>
          最終更新: {result?.updatedAt ? new Date(result.updatedAt).toLocaleString() : "-"}
        </p>
      </aside>
    </div>
  );
}
