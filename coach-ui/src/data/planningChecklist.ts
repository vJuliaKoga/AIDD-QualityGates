import { ChecklistNode } from "@/lib/coachTypes";

export const planningPhase = {
  id: "planning" as const,
  name: "企画",
  description: "品質ゲートを順番に確認し、企画フェーズの妥当性を判断します。",
};

export const planningChecklist: ChecklistNode[] = [
  {
    id: "planning-001",
    title: "目的・背景の明確化",
    description: "誰のどの課題を解くか、なぜ今取り組むのかを整理する。",
    examples: {
      pass: ["対象ユーザーと課題が具体的に記述されている", "着手理由が定量的に説明されている"],
      fail: ["背景が抽象的で、検証可能な根拠がない"],
      abort: ["そもそも現時点で取り組む必然性がない"],
    },
    unlocks: ["planning-002"],
  },
  {
    id: "planning-002",
    title: "成功条件の定義",
    description: "KPI と品質基準を定義し、達成判定ができる状態にする。",
    examples: {
      pass: ["KPI が数値で定義されている", "品質観点がチェック可能な粒度で列挙されている"],
      fail: ["成功条件が曖昧で、判定者に依存してしまう"],
      abort: ["測定方法がなく進捗評価ができない"],
    },
    unlocks: ["planning-003"],
  },
  {
    id: "planning-003",
    title: "スコープ/非スコープ整理",
    description: "今回実施する範囲と実施しない範囲を明確に分離する。",
    examples: {
      pass: ["非スコープが明確に明文化されている"],
      fail: ["要望追加によりスコープが無制限に広がっている"],
    },
    unlocks: ["planning-004"],
  },
  {
    id: "planning-004",
    title: "主要リスクと対応方針",
    description: "想定リスクを洗い出し、予防策とエスカレーション条件を決める。",
    examples: {
      pass: ["リスクごとに担当者と対策が設定されている"],
      fail: ["リスクの列挙のみで対応方針がない"],
      abort: ["重大リスクの制御方法がなく実行不能"],
    },
    unlocks: ["planning-005"],
  },
  {
    id: "planning-005",
    title: "レビュー体制の合意",
    description: "意思決定者・確認者・承認フローを確定し、運用可能にする。",
    examples: {
      pass: ["レビュー担当と承認者が明示されている"],
      fail: ["責任者が不明で判断が滞留する"],
      abort: ["レビュー体制が構築できず品質責任が持てない"],
    },
    unlocks: [],
  },
];
