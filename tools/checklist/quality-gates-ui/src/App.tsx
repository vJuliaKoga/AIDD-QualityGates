import React, { useState, useEffect } from 'react';

// --- Types ---
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
  checkedItems: Record<string, boolean>;
}

interface LogEvent {
  eventId: string;
  nodeId: string;
  fromStatus: Status;
  toStatus: Status;
  actorName: string;
  reason: string | null;
  occurredAtLocal: string;
}

// --- Mock Data ---
const mockTemplate: TemplateNode[] = [
  {
    nodeId: 'P-001',
    title: '目的の明確化',
    description: 'この企画で何を達成するかを明文化する。',
    detailedChecks: [
      { checkId: 'P-001-C1', text: '目的・KPIが1枚で説明できるか', checked: false },
      { checkId: 'P-001-C2', text: '対象範囲（スコープ）が明確か', checked: false },
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
  const [nodes, setNodes] = useState<TemplateNode[]>(mockTemplate);
  const [nodeStates, setNodeStates] = useState<Record<string, NodeState>>({});
  const [visibleNodes, setVisibleNodes] = useState<string[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  
  const [logEvents, setLogEvents] = useState<LogEvent[]>([]);
  const [actorName, setActorName] = useState('');
  const [pendingReason, setPendingReason] = useState('');

  const [lastNodeId, setLastNodeId] = useState<string>('P-004');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [customTitle, setCustomTitle] = useState('');
  const [customDesc, setCustomDesc] = useState('');

  useEffect(() => {
    const initialVisible = nodes.filter(n => n.ui.initialVisible).map(n => n.nodeId);
    setVisibleNodes(initialVisible);
    
    const initialStates: Record<string, NodeState> = {};
    nodes.forEach(n => {
      const initialChecked: Record<string, boolean> = {};
      n.detailedChecks.forEach(check => {
        initialChecked[check.checkId] = check.checked;
      });

      initialStates[n.nodeId] = {
        status: 'ToDo',
        pendingReason: null,
        actorName: null,
        riskLevel: 'C',
        updatedAtLocal: null,
        checkedItems: initialChecked,
      };
    });
    setNodeStates(initialStates);
  }, []); 

  const handleCheckChange = (nodeId: string, checkId: string, isChecked: boolean) => {
    setNodeStates(prev => ({
      ...prev,
      [nodeId]: {
        ...prev[nodeId],
        checkedItems: {
          ...prev[nodeId].checkedItems,
          [checkId]: isChecked
        },
        updatedAtLocal: new Date().toISOString()
      }
    }));
  };

  // カスタムノード用のテキスト編集ハンドラ
  const handleCustomCheckTextChange = (nodeId: string, checkId: string, newText: string) => {
    setNodes(prev => prev.map(n => {
      if (n.nodeId === nodeId) {
        return {
          ...n,
          detailedChecks: n.detailedChecks.map(c => 
            c.checkId === checkId ? { ...c, text: newText } : c
          )
        };
      }
      return n;
    }));
  };

  // リスクレベル変更ハンドラ
  const handleRiskLevelChange = (nodeId: string, newRiskLevel: RiskLevel) => {
    setNodeStates(prev => ({
      ...prev,
      [nodeId]: {
        ...prev[nodeId],
        riskLevel: newRiskLevel,
        updatedAtLocal: new Date().toISOString()
      }
    }));
  };

  const handleStatusChange = (nodeId: string, newStatus: Status) => {
    if (!actorName.trim()) {
      alert('実施者名（確認者名）を入力してください。');
      return;
    }
    if (newStatus === 'Pending' && !pendingReason.trim()) {
      alert('Pending理由を入力してください。');
      return;
    }

    const currentState = nodeStates[nodeId];
    const timestamp = new Date().toISOString();

    setNodeStates(prev => ({
      ...prev,
      [nodeId]: {
        ...prev[nodeId],
        status: newStatus,
        pendingReason: newStatus === 'Pending' ? pendingReason : prev[nodeId].pendingReason,
        actorName: actorName,
        updatedAtLocal: timestamp,
      }
    }));

    const newLogEvent: LogEvent = {
      eventId: `evt-${crypto.randomUUID()}`,
      nodeId: nodeId,
      fromStatus: currentState.status,
      toStatus: newStatus,
      actorName: actorName,
      reason: newStatus === 'Pending' ? pendingReason : null,
      occurredAtLocal: timestamp,
    };
    setLogEvents(prev => [...prev, newLogEvent]);

    if (newStatus === 'Done' || newStatus === 'Pending') {
      const node = nodes.find(n => n.nodeId === nodeId);
      if (node && node.unlocks.length > 0) {
        setTimeout(() => {
          setVisibleNodes(prev => {
            const newVisible = new Set(prev);
            node.unlocks.forEach(id => newVisible.add(id));
            return Array.from(newVisible);
          });
        }, 500);
      }
      if (newStatus === 'Done') setSelectedNodeId(null);
    }
  };

  const handleAddCustomNode = () => {
    if (!customTitle.trim()) {
      alert('タイトルは必須です。');
      return;
    }

    const newNodeId = `CUSTOM-${crypto.randomUUID().slice(0, 8).toUpperCase()}`;
    
    // 5行の空のチェックリストを生成
    const newChecks = Array.from({ length: 5 }).map((_, i) => ({
      checkId: `${newNodeId}-C${i + 1}`,
      text: '',
      checked: false
    }));

    const newNode: TemplateNode = {
      nodeId: newNodeId,
      title: customTitle,
      description: customDesc,
      detailedChecks: newChecks,
      unlocks: [],
      ui: { initialVisible: false },
      isCustom: true
    };

    setNodes(prev => prev.map(n => 
      n.nodeId === lastNodeId ? { ...n, unlocks: [...n.unlocks, newNodeId] } : n
    ).concat(newNode));

    const initialChecked: Record<string, boolean> = {};
    newChecks.forEach(c => { initialChecked[c.checkId] = false; });

    setNodeStates(prev => ({
      ...prev,
      [newNodeId]: {
        status: 'ToDo',
        pendingReason: null,
        actorName: null,
        riskLevel: 'C',
        updatedAtLocal: null,
        checkedItems: initialChecked
      }
    }));

    setTimeout(() => {
      setVisibleNodes(prev => [...prev, newNodeId]);
    }, 100);

    setLastNodeId(newNodeId);
    setIsModalOpen(false);
    setCustomTitle('');
    setCustomDesc('');
  };

  const handleExportJSON = () => {
    const exportData = {
      exportVersion: "1.0",
      templateId: "QG-PLAN-001",
      templateVersion: "0.1.0",
      phaseId: "planning",
      exportedAtLocal: new Date().toISOString(),
      actor: { displayName: actorName || "未入力", actorId: null },
      nodes: nodeStates,
      customNodeDefinitions: nodes.filter(n => n.isCustom), // カスタム定義も保存
      logEvents: logEvents
    };

    const jsonString = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `coach-ui-export-${new Date().getTime()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const selectedNode = nodes.find(n => n.nodeId === selectedNodeId);
  const selectedState = selectedNodeId ? nodeStates[selectedNodeId] : null;

  const allPredefinedDone = mockTemplate.every(n => {
    const st = nodeStates[n.nodeId]?.status;
    return st === 'Done' || st === 'Pending';
  });
  const lastNodeState = nodeStates[lastNodeId]?.status;
  // 上限撤廃：最後のノードが完了していれば常に表示
  const showAddButton = allPredefinedDone && (lastNodeState === 'Done' || lastNodeState === 'Pending');

  return (
    <div className="flex h-screen w-full bg-[#0B0F19] text-slate-200 overflow-hidden font-sans">
      
      <div className="absolute top-0 left-0 p-6 z-10 w-full flex justify-between pointer-events-none">
        <div>
          <h1 className="text-xl font-bold text-blue-400 tracking-wider">Coach UI <span className="text-sm text-slate-500 font-normal">| PLANNING PHASE</span></h1>
        </div>
        <button 
          onClick={handleExportJSON}
          className="pointer-events-auto px-4 py-2 bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/30 text-indigo-300 rounded shadow-lg transition-all text-sm font-medium flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
          JSONエクスポート
        </button>
      </div>

      <div className="flex-1 relative overflow-auto p-24 flex items-center justify-start min-w-max">
        <div className="flex items-center gap-16 relative pl-12 pr-32">
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

          {showAddButton && (
            <div 
              className="relative z-10 w-20 h-20 flex items-center justify-center rounded-xl border-2 border-dashed border-indigo-500/50 hover:bg-indigo-900/30 hover:border-blue-400 cursor-pointer transition-all opacity-100 animate-[fade-in_0.5s_ease-out]" 
              onClick={() => setIsModalOpen(true)}
            >
              <span className="text-3xl text-indigo-400">+</span>
              <svg className="absolute top-1/2 right-full w-16 h-2 -translate-y-1/2 overflow-visible z-0">
                  <line x1="0" y1="0" x2="64" y2="0" stroke="#10B981" strokeWidth="2" strokeDasharray="4 4" className="animate-[draw_0.5s_ease-out_forwards]" />
              </svg>
            </div>
          )}
        </div>
      </div>

      <div className={`
        w-[450px] bg-[#0F1423] border-l border-slate-800 shadow-2xl transition-transform duration-300 ease-in-out flex flex-col z-20
        ${selectedNodeId ? 'translate-x-0' : 'translate-x-full absolute right-0 h-full'}
      `}>
        {selectedNode && selectedState && (
          <>
            <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
              <h2 className="text-lg font-bold text-slate-100">{selectedNode.title}</h2>
              <button onClick={() => setSelectedNodeId(null)} className="text-slate-500 hover:text-slate-300 text-xl font-bold">✕</button>
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

              {selectedNode.description && (
                <div className="p-4 bg-indigo-950/20 border border-indigo-900/50 rounded-lg">
                  <p className="text-sm text-slate-300 leading-relaxed">{selectedNode.description}</p>
                </div>
              )}

              {/* リスクレベル変更UI */}
              <div className="space-y-2">
                <label className="text-xs text-slate-500 font-semibold uppercase tracking-wider">リスクレベル</label>
                <div className="flex gap-2">
                  {(['S', 'A', 'B', 'C'] as RiskLevel[]).map(risk => (
                    <button
                      key={risk}
                      onClick={() => handleRiskLevelChange(selectedNode.nodeId, risk)}
                      className={`flex-1 py-1.5 text-sm font-bold rounded border transition-all ${
                        selectedState.riskLevel === risk
                          ? risk === 'S' ? 'bg-red-900/40 border-red-500 text-red-400' 
                          : risk === 'A' ? 'bg-orange-900/40 border-orange-500 text-orange-400'
                          : risk === 'B' ? 'bg-yellow-900/40 border-yellow-500 text-yellow-400'
                          : 'bg-blue-900/40 border-blue-500 text-blue-400'
                          : 'bg-[#1A2235] border-slate-700 text-slate-500 hover:border-slate-500'
                      }`}
                    >
                      {risk}
                    </button>
                  ))}
                </div>
              </div>

              {selectedNode.detailedChecks.length > 0 && (
                <div className="space-y-3">
                  <label className="text-xs text-slate-500 font-semibold uppercase tracking-wider">詳細チェック項目</label>
                  {selectedNode.detailedChecks.map(check => (
                    <label key={check.checkId} className={`flex items-start gap-3 p-3 bg-[#1A2235] rounded border transition-colors ${selectedNode.isCustom ? 'border-indigo-900/50 hover:border-indigo-500' : 'border-slate-800 hover:bg-slate-800 cursor-pointer'}`}>
                      <input 
                        type="checkbox" 
                        checked={selectedState.checkedItems[check.checkId] || false}
                        onChange={(e) => handleCheckChange(selectedNode.nodeId, check.checkId, e.target.checked)}
                        className="mt-1 accent-blue-600 bg-slate-800 border-slate-700 cursor-pointer" 
                      />
                      {selectedNode.isCustom ? (
                        <input
                          type="text"
                          value={check.text}
                          onChange={(e) => handleCustomCheckTextChange(selectedNode.nodeId, check.checkId, e.target.value)}
                          placeholder="チェック項目を入力..."
                          className="w-full bg-transparent border-b border-transparent focus:border-blue-500 focus:outline-none text-sm text-slate-200 placeholder-slate-600"
                        />
                      ) : (
                        <span className="text-sm text-slate-300">{check.text}</span>
                      )}
                    </label>
                  ))}
                </div>
              )}

              <div className="space-y-2 pt-2 border-t border-slate-800">
                <label className="text-xs text-slate-500 font-semibold uppercase tracking-wider">ステータス更新</label>
                <div className="grid grid-cols-2 gap-2">
                  <button onClick={() => handleStatusChange(selectedNode.nodeId, 'InProgress')} className="py-2 bg-[#1A2235] hover:bg-blue-900/30 border border-slate-700 hover:border-blue-500 text-sm rounded transition-colors text-slate-300">InProgress</button>
                  <button onClick={() => handleStatusChange(selectedNode.nodeId, 'Done')} className="py-2 bg-emerald-600/20 hover:bg-emerald-600/40 border border-emerald-600/50 text-emerald-400 text-sm rounded transition-colors">Done (完了)</button>
                  <button onClick={() => handleStatusChange(selectedNode.nodeId, 'Pending')} className="py-2 bg-amber-600/20 hover:bg-amber-600/40 border border-amber-600/50 text-amber-400 text-sm rounded transition-colors col-span-2">Pending (保留して進む)</button>
                </div>
              </div>

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

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-[#0F1423] border border-slate-800 rounded-xl p-8 w-[400px] shadow-2xl">
            <h2 className="text-xl font-bold text-slate-100 mb-6">カスタム項目の追加</h2>
            
            <div className="space-y-4 mb-8">
              <div>
                <label className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2 block">タイトル (必須)</label>
                <input 
                  type="text" 
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  placeholder="例: 特定環境での動作確認"
                  maxLength={100}
                  className="w-full bg-[#1A2235] border border-slate-700 rounded p-3 text-sm focus:outline-none focus:border-blue-500 transition-colors text-slate-200"
                />
              </div>
              <div>
                <label className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2 block">説明 (任意)</label>
                <textarea 
                  value={customDesc}
                  onChange={(e) => setCustomDesc(e.target.value)}
                  placeholder="検証の目的や基準を記載"
                  maxLength={500}
                  className="w-full bg-[#1A2235] border border-slate-700 rounded p-3 text-sm focus:outline-none focus:border-blue-500 min-h-[100px] text-slate-200"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setIsModalOpen(false)}
                className="px-5 py-2 rounded text-sm font-medium text-slate-400 hover:bg-slate-800 transition-colors"
              >
                キャンセル
              </button>
              <button 
                onClick={handleAddCustomNode}
                className="px-5 py-2 rounded text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white transition-colors"
              >
                追加する
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}