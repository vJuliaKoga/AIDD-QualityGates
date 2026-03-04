"use client";

type ExportButtonProps = {
  onExport: () => void;
  disabled?: boolean;
};

export function ExportButton({ onExport, disabled = false }: ExportButtonProps) {
  return (
    <button
      type="button"
      onClick={onExport}
      disabled={disabled}
      style={{
        position: "fixed",
        top: 16,
        left: 16,
        zIndex: 30,
        border: "1px solid #12324f",
        borderRadius: 10,
        padding: "10px 14px",
        background: disabled ? "#d3dbe5" : "#f4f7fb",
        color: "#12324f",
        fontWeight: 700,
        cursor: disabled ? "not-allowed" : "pointer",
      }}
    >
      JSONエクスポート
    </button>
  );
}
