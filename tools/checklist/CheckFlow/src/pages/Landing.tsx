import { useState, useEffect, useRef, useCallback } from "react";

const API = "http://localhost:3001/api";

// --- Gear drawing ---
function drawGear(ctx, cx, cy, innerR, outerR, teeth, rotation, strokeColor, lineWidth = 1.5) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(rotation);
  ctx.beginPath();
  const step = (Math.PI * 2) / teeth;
  const tipW = step * 0.28;
  const baseW = step * 0.36;
  for (let i = 0; i < teeth; i++) {
    const angle = i * step;
    ctx.lineTo(Math.cos(angle - baseW / 2) * innerR, Math.sin(angle - baseW / 2) * innerR);
    ctx.lineTo(Math.cos(angle - tipW / 2) * outerR, Math.sin(angle - tipW / 2) * outerR);
    ctx.lineTo(Math.cos(angle + tipW / 2) * outerR, Math.sin(angle + tipW / 2) * outerR);
    ctx.lineTo(Math.cos(angle + baseW / 2) * innerR, Math.sin(angle + baseW / 2) * innerR);
  }
  ctx.closePath();
  ctx.strokeStyle = strokeColor;
  ctx.lineWidth = lineWidth;
  ctx.stroke();
  ctx.beginPath(); ctx.arc(0, 0, innerR * 0.3, 0, Math.PI * 2); ctx.stroke();
  ctx.beginPath(); ctx.arc(0, 0, 3, 0, Math.PI * 2); ctx.stroke();
  ctx.restore();
}

const GEARS = [
  { teeth: 20, innerR: 58, outerR: 72 },
  { teeth: 14, innerR: 40, outerR: 52 },
  { teeth: 18, innerR: 52, outerR: 65 },
  { teeth: 12, innerR: 35, outerR: 46 },
  { teeth: 16, innerR: 46, outerR: 58 },
];
const HL = 3;

export default function Landing({ onStart }) {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const timeRef = useRef(0);
  const [phase, setPhase] = useState("hero");
  const [dims, setDims] = useState({ w: 0, h: 0 });

  const [currentUser, setCurrentUser] = useState(null);
  const [users, setUsers] = useState([]);

  // Login
  const [loginName, setLoginName] = useState("");
  const [loginPass, setLoginPass] = useState("");
  const [loginError, setLoginError] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);

  // Admin create user
  const [newName, setNewName] = useState("");
  const [newPass, setNewPass] = useState("");
  const [newRole, setNewRole] = useState("User");
  const [adminMsg, setAdminMsg] = useState({ type: "", text: "" });

  // Server connection status
  const [serverOk, setServerOk] = useState(true);

  // Check server on mount
  useEffect(() => {
    fetch(`${API}/health`).then(r => r.json()).then(() => setServerOk(true)).catch(() => setServerOk(false));
  }, []);

  // === API calls ===
  const apiLogin = async () => {
    if (!loginName.trim()) { setLoginError("ユーザー名を入力してください。"); return; }
    if (!loginPass.trim()) { setLoginError("パスワードを入力してください。"); return; }
    setLoginLoading(true);
    try {
      const res = await fetch(`${API}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: loginName.trim(), password: loginPass }),
      });
      const data = await res.json();
      if (!res.ok) { setLoginError(data.error); setLoginLoading(false); return; }
      setLoginError("");
      setCurrentUser(data);
      if (data.role === "Admin") {
        setPhase("adminMenu");
      } else {
        if (onStart) onStart({ username: data.username, role: data.role });
      }
    } catch {
      setLoginError("サーバーに接続できません。サーバーが起動しているか確認してください。");
    }
    setLoginLoading(false);
  };

  const apiLoadUsers = async () => {
    try {
      const res = await fetch(`${API}/users`);
      const data = await res.json();
      setUsers(data);
    } catch { /* silent */ }
  };

  const apiCreateUser = async () => {
    const name = newName.trim();
    if (!name) { setAdminMsg({ type: "error", text: "ユーザー名を入力してください。" }); return; }
    if (name.length > 30) { setAdminMsg({ type: "error", text: "30文字以内で入力してください。" }); return; }
    if (!newPass.trim()) { setAdminMsg({ type: "error", text: "初期パスワードを設定してください。" }); return; }
    if (newPass.trim().length < 3) { setAdminMsg({ type: "error", text: "パスワードは3文字以上にしてください。" }); return; }
    try {
      const res = await fetch(`${API}/users`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: name, password: newPass.trim(), role: newRole }),
      });
      const data = await res.json();
      if (!res.ok) { setAdminMsg({ type: "error", text: data.error }); return; }
      setAdminMsg({ type: "success", text: data.message });
      setNewName(""); setNewPass(""); setNewRole("User");
      apiLoadUsers();
    } catch {
      setAdminMsg({ type: "error", text: "サーバーに接続できません。" });
    }
  };

  const apiChangeRole = async (targetName, newRoleVal) => {
    try {
      const res = await fetch(`${API}/users/${encodeURIComponent(targetName)}/role`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: newRoleVal, requestedBy: currentUser?.username }),
      });
      const data = await res.json();
      if (!res.ok) { setAdminMsg({ type: "error", text: data.error }); return; }
      setAdminMsg({ type: "success", text: data.message });
      apiLoadUsers();
    } catch {
      setAdminMsg({ type: "error", text: "サーバーに接続できません。" });
    }
  };

  const apiDeleteUser = async (targetName) => {
    try {
      const res = await fetch(`${API}/users/${encodeURIComponent(targetName)}?requestedBy=${encodeURIComponent(currentUser?.username || "")}`, {
        method: "DELETE",
      });
      const data = await res.json();
      if (!res.ok) { setAdminMsg({ type: "error", text: data.error }); return; }
      setAdminMsg({ type: "success", text: data.message });
      apiLoadUsers();
    } catch {
      setAdminMsg({ type: "error", text: "サーバーに接続できません。" });
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setLoginName(""); setLoginPass(""); setLoginError("");
    setAdminMsg({ type: "", text: "" });
    setPhase("login");
  };

  const handleGetStarted = () => {
    setPhase("fadeOut");
    setTimeout(() => setPhase("login"), 600);
  };

  const openAdminDash = () => {
    setPhase("adminDash");
    setAdminMsg({ type: "", text: "" });
    apiLoadUsers();
  };

  // === Canvas ===
  const gearPos = useCallback((w, h) => {
    const cx = w * 0.5, cy = h * 0.48, sp = Math.min(w, h) * 0.008;
    const p = [];
    p.push({ x: cx - 70, y: cy - 60 });
    const d01 = GEARS[0].outerR + GEARS[1].outerR - 6 + sp;
    p.push({ x: p[0].x + d01 * Math.cos(0.6), y: p[0].y + d01 * Math.sin(0.6) });
    const d12 = GEARS[1].outerR + GEARS[2].outerR - 6 + sp;
    p.push({ x: p[1].x + d12 * Math.cos(-0.4), y: p[1].y + d12 * Math.sin(-0.4) });
    const d23 = GEARS[2].outerR + GEARS[3].outerR - 5 + sp;
    p.push({ x: p[2].x + d23 * Math.cos(1.2), y: p[2].y + d23 * Math.sin(1.2) });
    const d04 = GEARS[0].outerR + GEARS[4].outerR - 6 + sp;
    p.push({ x: p[0].x + d04 * Math.cos(2.4), y: p[0].y + d04 * Math.sin(2.4) });
    return p;
  }, []);

  useEffect(() => {
    const resize = () => setDims({ w: window.innerWidth, h: window.innerHeight });
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const { w, h } = dims;
    canvas.width = w * dpr; canvas.height = h * dpr;
    canvas.style.width = w + "px"; canvas.style.height = h + "px";
    ctx.scale(dpr, dpr);
    const pos = gearPos(w, h);
    const base = GEARS[0].teeth;
    const spd = GEARS.map((g, i) => (base / g.teeth) * (i % 2 === 0 ? 1 : -1) * 0.3);
    spd[4] = -(base / GEARS[4].teeth) * 0.3;
    const particles = Array.from({ length: 40 }, () => ({
      x: Math.random() * w, y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.3, vy: (Math.random() - 0.5) * 0.3,
      r: Math.random() * 1.5 + 0.5, a: Math.random() * 0.3 + 0.05,
    }));
    function frame() {
      timeRef.current += 0.008;
      const t = timeRef.current;
      ctx.clearRect(0, 0, w, h); ctx.fillStyle = "#000"; ctx.fillRect(0, 0, w, h);
      ctx.strokeStyle = "rgba(255,255,255,0.02)"; ctx.lineWidth = 0.5;
      for (let x = 0; x < w; x += 60) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
      for (let y = 0; y < h; y += 60) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
      particles.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = w; if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(100,140,220,${p.a})`; ctx.fill();
      });
      [[0,1],[1,2],[2,3],[0,4]].forEach(([a, b]) => {
        ctx.beginPath(); ctx.moveTo(pos[a].x, pos[a].y); ctx.lineTo(pos[b].x, pos[b].y);
        ctx.strokeStyle = "rgba(80,100,160,0.08)"; ctx.lineWidth = 1; ctx.stroke();
      });
      GEARS.forEach((g, i) => {
        const rot = t * spd[i], isH = i === HL;
        if (isH) {
          ctx.save(); ctx.shadowColor = "rgba(80,160,255,0.25)"; ctx.shadowBlur = 20;
          drawGear(ctx, pos[i].x, pos[i].y, g.innerR, g.outerR, g.teeth, rot, "rgba(80,160,255,0.7)", 1.8);
          ctx.restore();
        } else {
          drawGear(ctx, pos[i].x, pos[i].y, g.innerR, g.outerR, g.teeth, rot, "rgba(100,120,180,0.35)", 1.2);
        }
      });
      const grad = ctx.createRadialGradient(w / 2, h / 2, w * 0.2, w / 2, h / 2, w * 0.75);
      grad.addColorStop(0, "rgba(0,0,0,0)"); grad.addColorStop(1, "rgba(0,0,0,0.6)");
      ctx.fillStyle = grad; ctx.fillRect(0, 0, w, h);
      animRef.current = requestAnimationFrame(frame);
    }
    frame();
    return () => { if (animRef.current) cancelAnimationFrame(animRef.current); };
  }, [dims, gearPos]);

  // === Shared styles ===
  const inputStyle = {
    width: "100%", padding: "12px 14px", fontSize: 14,
    color: "rgba(210,220,240,0.9)", background: "rgba(15,20,40,0.6)",
    border: "1px solid rgba(60,90,160,0.2)", borderRadius: 6,
    outline: "none", boxSizing: "border-box", transition: "border-color 0.25s ease",
  };
  const labelStyle = {
    display: "block", fontSize: 10, fontWeight: 600,
    letterSpacing: "0.12em", textTransform: "uppercase",
    color: "rgba(140,160,200,0.5)", marginBottom: 8,
  };
  const cardStyle = {
    width: "100%", maxWidth: 400, padding: "40px 36px 36px",
    background: "rgba(8,12,24,0.8)", backdropFilter: "blur(24px)", WebkitBackdropFilter: "blur(24px)",
    border: "1px solid rgba(60,90,160,0.15)", borderRadius: 12,
    boxShadow: "0 0 60px rgba(20,40,100,0.15), 0 0 1px rgba(100,140,220,0.2)",
  };
  const wideCardStyle = { ...cardStyle, maxWidth: 520 };
  const focusIn = (e) => (e.target.style.borderColor = "rgba(80,140,240,0.5)");
  const focusOut = (e) => (e.target.style.borderColor = "rgba(60,90,160,0.2)");

  const btnBase = (active) => ({
    width: "100%", padding: "13px 0", fontSize: 13, fontWeight: 500,
    letterSpacing: "0.1em", textTransform: "uppercase",
    color: active ? "rgba(180,210,255,0.95)" : "rgba(120,140,180,0.35)",
    background: active ? "rgba(20,40,90,0.9)" : "rgba(20,30,60,0.4)",
    border: active ? "1px solid rgba(60,100,200,0.35)" : "1px solid rgba(60,90,160,0.1)",
    borderRadius: 6, cursor: active ? "pointer" : "default", transition: "all 0.3s ease",
  });
  const hoverBtn = (active) => ({
    onMouseEnter: e => { if (active) { e.currentTarget.style.background = "rgba(30,58,120,1)"; e.currentTarget.style.boxShadow = "0 0 24px rgba(40,80,180,0.35)"; } },
    onMouseLeave: e => { e.currentTarget.style.background = active ? "rgba(20,40,90,0.9)" : "rgba(20,30,60,0.4)"; e.currentTarget.style.boxShadow = "none"; },
  });

  const overlay = (show) => ({
    position: "absolute", inset: 0, zIndex: 20,
    display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
    padding: "0 24px",
    opacity: show ? 1 : 0, transform: show ? "translateY(0)" : "translateY(30px)",
    transition: "all 0.6s cubic-bezier(0.22,1,0.36,1) 0.1s",
    pointerEvents: show ? "auto" : "none",
  });

  const titleBlock = (sub) => (
    <div style={{ textAlign: "center", marginBottom: 28 }}>
      <h2 style={{ fontSize: 22, fontWeight: 300, color: "#fff", margin: "0 0 6px 0" }}>
        Check<span style={{ fontWeight: 600, color: "rgba(100,170,255,0.95)" }}>Flow</span>
      </h2>
      <p style={{ fontSize: 12, color: "rgba(140,160,200,0.45)", margin: 0, letterSpacing: "0.05em" }}>{sub}</p>
    </div>
  );

  const backBtn = (label, onClick) => (
    <button onClick={onClick}
      style={{ marginTop: 24, fontSize: 12, color: "rgba(120,150,200,0.35)", background: "none", border: "none", cursor: "pointer", letterSpacing: "0.05em", transition: "color 0.2s" }}
      onMouseEnter={e => (e.currentTarget.style.color = "rgba(120,150,200,0.65)")}
      onMouseLeave={e => (e.currentTarget.style.color = "rgba(120,150,200,0.35)")}
    >{label}</button>
  );

  const isHero = phase === "hero";

  return (
    <div style={{ position: "relative", width: "100vw", height: "100vh", overflow: "hidden", background: "#000", fontFamily: "'SF Pro Display',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif" }}>
      <canvas ref={canvasRef} style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%" }} />

      {/* ===== HERO ===== */}
      <div style={{
        position: "absolute", inset: 0, zIndex: 10,
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        textAlign: "center", padding: "0 24px",
        opacity: isHero ? 1 : 0, transform: isHero ? "translateY(0)" : "translateY(-20px)",
        transition: "all 0.55s cubic-bezier(0.4,0,0.2,1)", pointerEvents: isHero ? "auto" : "none",
      }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none" stroke="rgba(80,160,255,0.8)" strokeWidth="1.5">
            <circle cx="14" cy="14" r="5" /><circle cx="14" cy="14" r="10" strokeDasharray="4 3" />
          </svg>
          <span style={{ fontSize: 13, fontWeight: 500, letterSpacing: "0.2em", color: "rgba(120,160,220,0.6)", textTransform: "uppercase" }}>
            Score Aggregation Manager
          </span>
        </div>
        <h1 style={{ fontSize: "clamp(48px,8vw,96px)", fontWeight: 200, letterSpacing: "-0.03em", color: "#fff", margin: 0, lineHeight: 1.05 }}>
          Check<span style={{ fontWeight: 600, color: "rgba(100,170,255,0.95)" }}>Flow</span>
        </h1>
        <p style={{ fontSize: "clamp(14px,1.8vw,18px)", fontWeight: 300, color: "rgba(180,195,220,0.55)", maxWidth: 520, lineHeight: 1.7, margin: "24px 0 48px 0" }}>
          Template-driven quality gate engine.<br />Audit-ready checklists with traceable evidence.
        </p>
        <button onClick={handleGetStarted}
          onMouseEnter={e => { e.currentTarget.style.background = "rgba(30,58,120,0.95)"; e.currentTarget.style.borderColor = "rgba(80,140,240,0.5)"; e.currentTarget.style.boxShadow = "0 0 30px rgba(40,80,180,0.3)"; }}
          onMouseLeave={e => { e.currentTarget.style.background = "rgba(20,40,90,0.85)"; e.currentTarget.style.borderColor = "rgba(60,100,200,0.3)"; e.currentTarget.style.boxShadow = "0 0 20px rgba(30,60,140,0.15)"; }}
          style={{
            padding: "14px 52px", fontSize: 14, fontWeight: 500, letterSpacing: "0.12em", textTransform: "uppercase",
            color: "rgba(180,210,255,0.95)", background: "rgba(20,40,90,0.85)",
            border: "1px solid rgba(60,100,200,0.3)", borderRadius: 6, cursor: "pointer",
            transition: "all 0.35s ease", boxShadow: "0 0 20px rgba(30,60,140,0.15)",
          }}
        >Get Started</button>

        {/* Server status */}
        {!serverOk && (
          <p style={{ fontSize: 11, color: "rgba(255,120,100,0.7)", marginTop: 20 }}>
            ⚠ APIサーバーに接続できません。server/ で npm start を実行してください。
          </p>
        )}

        <div style={{ position: "absolute", bottom: 32, left: 0, right: 0, display: "flex", justifyContent: "center", gap: 32 }}>
          {["Template-driven", "Audit Trail", "CI-ready", "Offline PWA"].map(tag => (
            <span key={tag} style={{ fontSize: 11, fontWeight: 400, letterSpacing: "0.08em", color: "rgba(120,140,180,0.35)", textTransform: "uppercase" }}>{tag}</span>
          ))}
        </div>
      </div>

      {/* ===== LOGIN ===== */}
      <div style={overlay(phase === "login")}>
        <div style={cardStyle}>
          {titleBlock("Sign in to continue")}
          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Username</label>
            <input type="text" value={loginName} onChange={e => { setLoginName(e.target.value); setLoginError(""); }}
              placeholder="Enter your name" onKeyDown={e => e.key === "Enter" && apiLogin()}
              style={inputStyle} onFocus={focusIn} onBlur={focusOut} />
          </div>
          <div style={{ marginBottom: 8 }}>
            <label style={labelStyle}>Password</label>
            <input type="password" value={loginPass} onChange={e => { setLoginPass(e.target.value); setLoginError(""); }}
              placeholder="••••••••" onKeyDown={e => e.key === "Enter" && apiLogin()}
              style={inputStyle} onFocus={focusIn} onBlur={focusOut} />
          </div>
          {loginError && <p style={{ fontSize: 11, color: "rgba(255,120,100,0.85)", margin: "12px 0 0 0", lineHeight: 1.5 }}>{loginError}</p>}
          <button onClick={apiLogin} disabled={loginLoading}
            {...hoverBtn(!!(loginName.trim() && loginPass.trim()))}
            style={{ ...btnBase(!!(loginName.trim() && loginPass.trim())), marginTop: 20, opacity: loginLoading ? 0.5 : 1 }}>
            {loginLoading ? "Signing in..." : "Sign In"}
          </button>
        </div>
        {backBtn("← Back", () => setPhase("hero"))}
      </div>

      {/* ===== ADMIN MENU ===== */}
      <div style={overlay(phase === "adminMenu")}>
        <div style={cardStyle}>
          {titleBlock(`Welcome, ${currentUser?.username || ""}`)}
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 6, padding: "4px 12px",
            borderRadius: 4, fontSize: 10, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase",
            color: "rgba(255,180,100,0.9)", background: "rgba(255,150,50,0.1)",
            border: "1px solid rgba(255,150,50,0.2)", marginBottom: 28,
          }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            Admin
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <button
              onClick={() => { if (onStart) onStart({ username: currentUser.username, role: currentUser.role }); }}
              onMouseEnter={e => { e.currentTarget.style.background = "rgba(30,58,120,1)"; e.currentTarget.style.boxShadow = "0 0 24px rgba(40,80,180,0.3)"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "rgba(20,40,90,0.9)"; e.currentTarget.style.boxShadow = "none"; }}
              style={{
                width: "100%", padding: "14px 0", fontSize: 13, fontWeight: 500,
                letterSpacing: "0.1em", textTransform: "uppercase",
                color: "rgba(180,210,255,0.95)", background: "rgba(20,40,90,0.9)",
                border: "1px solid rgba(60,100,200,0.35)", borderRadius: 6,
                cursor: "pointer", transition: "all 0.3s ease",
              }}
            >Start Checklist</button>
            <button onClick={openAdminDash}
              onMouseEnter={e => (e.currentTarget.style.borderColor = "rgba(255,180,100,0.4)")}
              onMouseLeave={e => (e.currentTarget.style.borderColor = "rgba(255,150,50,0.15)")}
              style={{
                width: "100%", padding: "14px 0", fontSize: 13, fontWeight: 500,
                letterSpacing: "0.1em", textTransform: "uppercase",
                color: "rgba(255,200,140,0.8)", background: "transparent",
                border: "1px solid rgba(255,150,50,0.15)", borderRadius: 6,
                cursor: "pointer", transition: "all 0.3s ease",
              }}
            >Admin Dashboard</button>
          </div>
        </div>
        {backBtn("← Logout", handleLogout)}
      </div>

      {/* ===== ADMIN DASHBOARD ===== */}
      <div style={{
        ...overlay(phase === "adminDash"),
        overflowY: "auto", paddingTop: 40, paddingBottom: 40, justifyContent: "flex-start",
      }}>
        <div style={{ ...wideCardStyle, marginTop: "auto", marginBottom: "auto" }}>
          {titleBlock("Admin Dashboard")}

          {/* Create User */}
          <div style={{ marginBottom: 28, paddingBottom: 24, borderBottom: "1px solid rgba(60,90,160,0.1)" }}>
            <label style={{ ...labelStyle, fontSize: 11, marginBottom: 16, color: "rgba(255,180,100,0.6)" }}>Create New User</label>
            <div style={{ display: "flex", gap: 10, marginBottom: 10 }}>
              <div style={{ flex: 1 }}>
                <label style={labelStyle}>Username</label>
                <input type="text" value={newName} onChange={e => { setNewName(e.target.value); setAdminMsg({ type: "", text: "" }); }}
                  placeholder="New username" style={inputStyle} onFocus={focusIn} onBlur={focusOut} />
              </div>
              <div style={{ flex: 1 }}>
                <label style={labelStyle}>Password</label>
                <input type="text" value={newPass} onChange={e => { setNewPass(e.target.value); setAdminMsg({ type: "", text: "" }); }}
                  placeholder="Initial password" style={inputStyle} onFocus={focusIn} onBlur={focusOut} />
              </div>
            </div>
            <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
              <div style={{ flex: 1 }}>
                <label style={labelStyle}>Role</label>
                <div style={{ display: "flex", gap: 6 }}>
                  {["User", "Admin"].map(r => (
                    <button key={r} onClick={() => setNewRole(r)}
                      style={{
                        flex: 1, padding: "10px 0", fontSize: 12, fontWeight: 600,
                        letterSpacing: "0.08em", textTransform: "uppercase", borderRadius: 6,
                        cursor: "pointer", transition: "all 0.25s ease",
                        color: newRole === r ? (r === "Admin" ? "rgba(255,180,100,0.9)" : "rgba(100,170,255,0.9)") : "rgba(140,160,200,0.35)",
                        background: newRole === r ? (r === "Admin" ? "rgba(255,150,50,0.1)" : "rgba(60,100,200,0.1)") : "rgba(15,20,40,0.4)",
                        border: newRole === r ? (r === "Admin" ? "1px solid rgba(255,150,50,0.3)" : "1px solid rgba(60,100,200,0.3)") : "1px solid rgba(60,90,160,0.1)",
                      }}
                    >{r}</button>
                  ))}
                </div>
              </div>
              <div style={{ flex: 1 }}>
                <button onClick={apiCreateUser} {...hoverBtn(!!(newName.trim() && newPass.trim()))}
                  style={{ ...btnBase(!!(newName.trim() && newPass.trim())), padding: "10px 0", fontSize: 12 }}>
                  Create User
                </button>
              </div>
            </div>
            {adminMsg.text && (
              <p style={{ fontSize: 11, color: adminMsg.type === "error" ? "rgba(255,120,100,0.85)" : "rgba(100,220,160,0.85)", margin: "12px 0 0 0", lineHeight: 1.5 }}>{adminMsg.text}</p>
            )}
          </div>

          {/* User List */}
          <div>
            <label style={{ ...labelStyle, marginBottom: 12 }}>Registered Users ({users.length})</label>
            <div style={{ maxHeight: 260, overflowY: "auto" }}>
              {users.map((u) => (
                <div key={u.username} style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  padding: "10px 14px", marginBottom: 6, borderRadius: 8,
                  background: "rgba(15,20,40,0.5)", border: "1px solid rgba(60,90,160,0.08)",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontSize: 14, color: "rgba(210,220,240,0.85)", fontWeight: 500 }}>{u.username}</span>
                    <span style={{
                      fontSize: 9, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase",
                      padding: "3px 8px", borderRadius: 4,
                      color: u.role === "Admin" ? "rgba(255,180,100,0.9)" : "rgba(140,170,220,0.6)",
                      background: u.role === "Admin" ? "rgba(255,150,50,0.1)" : "rgba(60,100,200,0.08)",
                      border: u.role === "Admin" ? "1px solid rgba(255,150,50,0.2)" : "1px solid rgba(60,100,200,0.1)",
                    }}>{u.role}</span>
                  </div>
                  <div style={{ display: "flex", gap: 6 }}>
                    <button onClick={() => apiChangeRole(u.username, u.role === "Admin" ? "User" : "Admin")}
                      title={u.role === "Admin" ? "Userに降格" : "Adminに昇格"}
                      style={{
                        padding: "4px 10px", fontSize: 10, fontWeight: 500,
                        color: "rgba(140,170,220,0.6)", background: "rgba(60,100,200,0.06)",
                        border: "1px solid rgba(60,100,200,0.12)", borderRadius: 4,
                        cursor: "pointer", transition: "all 0.2s", letterSpacing: "0.05em",
                      }}
                      onMouseEnter={e => (e.currentTarget.style.borderColor = "rgba(80,140,240,0.4)")}
                      onMouseLeave={e => (e.currentTarget.style.borderColor = "rgba(60,100,200,0.12)")}
                    >{u.role === "Admin" ? "→ User" : "→ Admin"}</button>
                    <button onClick={() => apiDeleteUser(u.username)} title="削除"
                      style={{
                        padding: "4px 8px", fontSize: 10, fontWeight: 500,
                        color: "rgba(255,120,100,0.5)", background: "transparent",
                        border: "1px solid rgba(255,100,80,0.1)", borderRadius: 4,
                        cursor: "pointer", transition: "all 0.2s",
                      }}
                      onMouseEnter={e => { e.currentTarget.style.borderColor = "rgba(255,100,80,0.4)"; e.currentTarget.style.color = "rgba(255,120,100,0.9)"; }}
                      onMouseLeave={e => { e.currentTarget.style.borderColor = "rgba(255,100,80,0.1)"; e.currentTarget.style.color = "rgba(255,120,100,0.5)"; }}
                    >✕</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        {backBtn("← Back to Menu", () => { setPhase("adminMenu"); setAdminMsg({ type: "", text: "" }); })}
      </div>
    </div>
  );
}
