import React, { useState, useEffect, useRef } from 'react';

// --- Types (仕様書 21.9 ドメインモデルに基づく) ---
type Status = 'ToDo' | 'InProgress' | 'Pending' | 'Done';
type RiskLevel = 'S' | 'A' | 'B' | 'C';

interface TemplateNode {
  nodeId: string;
  title: string;
  description: string;
  detailedChecks: { checkId: string; text: string; checked: boolean }[];
  unlocks: string[];
  ui: { initialVisible: boolean };
  isCustom?: boolean;
}

interface NodeState {
  status: Status;
  pendingReason: string | null;
  actorName: string | null;
  riskLevel: RiskLevel;
  updatedAtLocal: string | null;
}

// --- Mock Data (仕様書 21.9.2) ---
const mockTemplate: TemplateNode[] = [
  {
    nodeId: 'P-001',
    title: '目的の明確化',
    description: 'この企画で何を達成するかを明文化する。',
    detailedChecks: [
      { checkId: 'P-001-C1', text: '目的・KPIが1枚で説明できるか', checked: false },
    ],
    unlocks: ['P-002', 'P-003'],
    ui: { initialVisible: true },
  },
  {
    nodeId: 'P-002',
    title: 'ステークホルダー整理',
    description: '関係者と意思決定者を明確化する。',
    detailedChecks: [
      { checkId: 'P-002-C1', text: '承認者がアサインされているか', checked: false },
    ],
    unlocks: ['P-004'],
    ui: { initialVisible: false },
  },
  {
    nodeId: 'P-003',
    title: 'AIリスク評価',
    description: 'AI生成コンテンツの検証範囲を特定する。',
    detailedChecks: [
      { checkId: 'P-003-C1', text: 'ハルシネーションの許容度定義', checked: false },
    ],
    unlocks: ['P-004'],
    ui: { initialVisible: false },
  },
  {
    nodeId: 'P-004',
    title: '要件定義フェーズ移行判定',
    description: '次フェーズへ進むための最終ゲート。',
    detailedChecks: [],
    unlocks: [],
    ui: { initialVisible: false },
  }
];

export default function CoachUI() {
  const [nodes] = useState<TemplateNode[]>(mockTemplate);
  const [nodeStates, setNodeStates] = useState<Record<string, NodeState>>({});
  const [visibleNodes, setVisibleNodes] = useState<string[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  
  // 入力フォーム用ステート
  const [actorName, setActorName] = useState('');
  const [pendingReason, setPendingReason] = useState('');

  // 初期化 (initialVisible: true のものを表示)
  useEffect(() => {
    const initialVisible = nodes.filter(n => n.ui.initialVisible).map(n => n.nodeId);
    setVisibleNodes(initialVisible);
    
    const initialStates: Record<string, NodeState> = {};
    nodes.forEach(n => {
      initialStates[n.nodeId] = {
        status: 'ToDo',
        pendingReason: null,
        actorName: null,
        riskLevel: 'C',
        updatedAtLocal: null,
      };
    });
    setNodeStates(initialStates);
  }, [nodes]);

  // ステータス更新処理 (仕様書 21.11.2 共通ルール)
  const handleStatusChange = (nodeId: string, newStatus: Status) => {
    if (!actorName.trim()) {
      alert('実施者名（確認者名）を入力してください。');
      return;
    }
    if (newStatus === 'Pending' && !pendingReason.trim()) {
      alert('Pending理由を入力してください。');
      return;
    }

    setNodeStates(prev => ({
      ...prev,
      [nodeId]: {
        ...prev[nodeId],
        status: newStatus,
        pendingReason: newStatus === 'Pending' ? pendingReason : prev[nodeId].pendingReason,
        actorName: actorName,
        updatedAtLocal: new Date().toISOString(),
      }
    }));

    // ノード解放ロジック (Done または Pending で解放)
    if (newStatus === 'Done' || newStatus === 'Pending') {
      const node = nodes.find(n => n.nodeId === nodeId);
      if (node && node.unlocks.length > 0) {
        setTimeout(() => {
          setVisibleNodes(prev => {
            const newVisible = new Set(prev);
            node.unlocks.forEach(id => newVisible.add(id));
            return Array.from(newVisible);
          });
        }, 500); // ぬるっと感を出すためのディレイ
      }
      if (newStatus === 'Done') setSelectedNodeId(null); // Done時はパネルを閉じる
    }
  };

  const selectedNode = nodes.find(n => n.nodeId === selectedNodeId);
  const selectedState = selectedNodeId ? nodeStates[selectedNodeId] : null;

  return (
    <div className="flex h-screen w-full bg-[#0B0F19] text-slate-200 overflow-hidden font-sans">
      
      {/* 画面ヘッダー部 / FR-040 エクスポート領域 */}
      <div className="absolute top-0 left-0 p-6 z-10 w-full flex justify-between pointer-events-none">
        <div>
          <h1 className="text-xl font-bold text-blue-400 tracking-wider">Coach UI <span className="text-sm text-slate-500 font-normal">| PLANNING PHASE</span></h1>
        </div>
        <button className="pointer-events-auto px-4 py-2 bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/30 text-indigo-300 rounded shadow-lg transition-all text-sm font-medium flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
          JSONエクスポート
        </button>
      </div>

      {/* マインドマップキャンバスエリア */}
      <div className="flex-1 relative overflow-auto p-24 flex items-center justify-center">
        <div className="flex items-center gap-16 relative">
          
          {/* ノードの描画 (モックアップ用簡易ツリー配置) */}
          {nodes.map((node) => {
            const isVisible = visibleNodes.includes(node.nodeId);
            const state = nodeStates[node.nodeId];
            if (!isVisible || !state) return null;

            const isDone = state.status === 'Done';
            const isPending = state.status === 'Pending';
            const isActive = selectedNodeId === node.nodeId;

            return (
              <div 
                key={node.nodeId}
                onClick={() => setSelectedNodeId(node.nodeId)}
                className={`
                  relative z-10 w-64 p-5 rounded-xl border cursor-pointer transition-all duration-500 ease-out transform
                  ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-10'}
                  ${isActive ? 'ring-2 ring-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.3)] bg-slate-800' : 'bg-[#151B2B] hover:bg-slate-800'}
                  ${isDone ? 'border-emerald-500/50' : isPending ? 'border-amber-500/50' : 'border-indigo-500/30'}
                `}
              >
                {/* 状態インジケータ */}
                <div className="flex justify-between items-start mb-3">
                  <span className="text-xs font-mono text-slate-500">{node.nodeId}</span>
                  <span className={`text-[10px] px-2 py-1 rounded tracking-wide font-bold uppercase
                    ${isDone ? 'bg-emerald-500/10 text-emerald-400' : 
                      isPending ? 'bg-amber-500/10 text-amber-400' : 
                      state.status === 'InProgress' ? 'bg-blue-500/10 text-blue-400' : 
                      'bg-slate-700/50 text-slate-400'}
                  `}>
                    {state.status}
                  </span>
                </div>
                <h3 className="font-semibold text-slate-100 mb-2">{node.title}</h3>
                
                {/* SVG 接続線 (次ノードへ) */}
                {node.unlocks.map(targetId => {
                   if (!visibleNodes.includes(targetId)) return null;
                   return (
                    <svg key={`${node.nodeId}-${targetId}`} className="absolute top-1/2 left-full w-16 h-2 -translate-y-1/2 overflow-visible z-0">
                      <line 
                        x1="0" y1="0" x2="64" y2="0" 
                        stroke={isDone ? "#10B981" : isPending ? "#F59E0B" : "#312E81"} 
                        strokeWidth="2" 
                        strokeDasharray={isPending ? "4 4" : "0"}
                        className="animate-[draw_0.5s_ease-out_forwards]"
                      />
                    </svg>
                   )
                })}
              </div>
            );
          })}
        </div>
      </div>

      {/* サイドパネル (SCR-003) */}
      <div className={`
        w-[450px] bg-[#0F1423] border-l border-slate-800 shadow-2xl transition-transform duration-300 ease-in-out flex flex-col
        ${selectedNodeId ? 'translate-x-0' : 'translate-x-full absolute right-0 h-full'}
      `}>
        {selectedNode && selectedState && (
          <>
            <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
              <h2 className="text-lg font-bold text-slate-100">{selectedNode.title}</h2>
              <button onClick={() => setSelectedNodeId(null)} className="text-slate-500 hover:text-slate-300">✕</button>
            </div>
            
            <div className="p-6 flex-1 overflow-y-auto space-y-6">
              <div className="space-y-2">
                <label className="text-xs text-slate-500 font-semibold uppercase tracking-wider">実施者 (必須)</label>
                <input 
                  type="text" 
                  value={actorName}
                  onChange={(e) => setActorName(e.target.value)}
                  placeholder="例: 山田太郎"
                  className="w-full bg-[#1A2235] border border-slate-700 rounded p-2 text-sm focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>

              <div className="p-4 bg-indigo-950/20 border border-indigo-900/50 rounded-lg">
                <p className="text-sm text-slate-300 leading-relaxed">{selectedNode.description}</p>
              </div>

              {selectedNode.detailedChecks.length > 0 && (
                <div className="space-y-3">
                  <label className="text-xs text-slate-500 font-semibold uppercase tracking-wider">詳細チェック項目</label>
                  {selectedNode.detailedChecks.map(check => (
                    <label key={check.checkId} className="flex items-start gap-3 p-3 bg-[#1A2235] rounded border border-slate-800 cursor-pointer hover:bg-slate-800 transition-colors">
                      <input type="checkbox" className="mt-1 accent-blue-600 bg-slate-800 border-slate-700" />
                      <span className="text-sm text-slate-300">{check.text}</span>
                    </label>
                  ))}
                </div>
              )}

              <div className="space-y-2">
                <label className="text-xs text-slate-500 font-semibold uppercase tracking-wider">ステータス更新</label>
                <div className="grid grid-cols-2 gap-2">
                  <button onClick={() => handleStatusChange(selectedNode.nodeId, 'InProgress')} className="py-2 bg-[#1A2235] hover:bg-blue-900/30 border border-slate-700 hover:border-blue-500 text-sm rounded transition-colors text-slate-300">InProgress</button>
                  <button onClick={() => handleStatusChange(selectedNode.nodeId, 'Done')} className="py-2 bg-emerald-600/20 hover:bg-emerald-600/40 border border-emerald-600/50 text-emerald-400 text-sm rounded transition-colors">Done (完了)</button>
                  <button onClick={() => handleStatusChange(selectedNode.nodeId, 'Pending')} className="py-2 bg-amber-600/20 hover:bg-amber-600/40 border border-amber-600/50 text-amber-400 text-sm rounded transition-colors col-span-2">Pending (保留して進む)</button>
                </div>
              </div>

              {/* Pending時のみ表示する理由入力欄 */}
              <div className={`transition-all duration-300 overflow-hidden ${selectedState.status === 'Pending' || pendingReason ? 'max-h-32 opacity-100' : 'max-h-0 opacity-0'}`}>
                <label className="text-xs text-amber-500 font-semibold uppercase tracking-wider mb-2 block">Pending 理由 (必須)</label>
                <textarea 
                  value={pendingReason}
                  onChange={(e) => setPendingReason(e.target.value)}
                  className="w-full bg-[#1A2235] border border-amber-900/50 rounded p-2 text-sm focus:outline-none focus:border-amber-500 min-h-[80px]"
                  placeholder="保留の理由と今後の対応方針を記載"
                />
              </div>

            </div>
          </>
        )}
      </div>

    </div>
  );
}