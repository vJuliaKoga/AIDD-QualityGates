export type UserRole = "Admin" | "User";

export type CoachSession = {
  username: string;
  role: UserRole;
  sessionId: string;
  loggedInAt: string;
};

export type ChecklistNode = {
  id: string;
  title: string;
  description?: string;
  examples?: {
    pass?: string[];
    fail?: string[];
    abort?: string[];
  };
  unlocks?: string[];
};

export type NodeStatus = "ToDo" | "InProgress" | "Pending" | "Done";

export type NodeResult = {
  nodeId: string;
  status: NodeStatus;
  checkedBy: string;
  updatedAt: string;
  reason?: string;
};

export type StatusChangeLog = {
  id: string;
  nodeId: string;
  from: NodeStatus | null;
  to: NodeStatus;
  checkedBy: string;
  updatedAt: string;
  reason?: string;
};

export type PhaseRun = {
  phaseId: "planning";
  sessionId: string;
  user: {
    username: string;
    role: UserRole;
  };
  startedAt: string;
  updatedAt: string;
  results: Record<string, NodeResult>;
  logs: StatusChangeLog[];
};
