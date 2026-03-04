"use client";

import { ChecklistNode, NodeResult, NodeStatus } from "@/lib/coachTypes";

type NodeCardProps = {
  node: ChecklistNode;
  result: NodeResult | null;
  isActive: boolean;
  onClick: () => void;
};

const statusColor: Record<NodeStatus, string> = {
  ToDo: "#64748b",
  InProgress: "#0f766e",
  Pending: "#c2410c",
  Done: "#14532d",
};

export function NodeCard({ node, result, isActive, onClick }: NodeCardProps) {
  const status = result?.status ?? "ToDo";

  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        width: "100%",
        textAlign: "left",
        border: isActive ? "2px solid #12324f" : "1px solid #d8dee7",
        borderRadius: 14,
        background: isActive ? "#f8fbff" : "#ffffff",
        padding: 14,
        display: "grid",
        gap: 8,
        cursor: "pointer",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
        <span style={{ fontWeight: 700, color: "#0f172a" }}>{node.title}</span>
        <span
          style={{
            fontSize: 12,
            borderRadius: 999,
            padding: "4px 10px",
            color: "#ffffff",
            background: statusColor[status],
            fontWeight: 700,
          }}
        >
          {status}
        </span>
      </div>
      {node.description ? <p style={{ margin: 0, color: "#334155" }}>{node.description}</p> : null}
      {result?.updatedAt ? (
        <p style={{ margin: 0, fontSize: 12, color: "#64748b" }}>更新: {new Date(result.updatedAt).toLocaleString()}</p>
      ) : null}
    </button>
  );
}
