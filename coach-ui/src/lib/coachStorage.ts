import { CoachSession, PhaseRun } from "@/lib/coachTypes";

export const SESSION_STORAGE_KEY = "coach.session";
export const PLANNING_PHASE_STORAGE_KEY = "coach.phase.planning";

const isBrowser = () => typeof window !== "undefined";

function readJson<T>(key: string): T | null {
  if (!isBrowser()) {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function writeJson<T>(key: string, value: T) {
  if (!isBrowser()) {
    return;
  }

  window.localStorage.setItem(key, JSON.stringify(value));
}

function removeKey(key: string) {
  if (!isBrowser()) {
    return;
  }

  window.localStorage.removeItem(key);
}

export function loadSession() {
  return readJson<CoachSession>(SESSION_STORAGE_KEY);
}

export function saveSession(session: CoachSession) {
  writeJson(SESSION_STORAGE_KEY, session);
}

export function clearSession() {
  removeKey(SESSION_STORAGE_KEY);
}

export function loadPlanningPhaseRun() {
  const rawRun = readJson<PhaseRun>(PLANNING_PHASE_STORAGE_KEY);
  if (!rawRun || rawRun.phaseId !== "planning") {
    return null;
  }
  return rawRun;
}

export function savePlanningPhaseRun(run: PhaseRun) {
  writeJson(PLANNING_PHASE_STORAGE_KEY, run);
}

export function clearPlanningPhaseRun() {
  removeKey(PLANNING_PHASE_STORAGE_KEY);
}
