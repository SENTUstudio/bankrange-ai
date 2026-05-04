import { getBranches, getBranchDetail } from '$lib/services/api.service';
import type { BranchSummary, BranchDetail } from '$lib/types/topology';
import { appState } from './appState.svelte';

export const branches = $state<Map<string, BranchSummary>>(new Map());
export const branchDetails = $state<Map<string, BranchDetail>>(new Map());

export function getSelectedBranch(): BranchDetail | null {
  return appState.selectedBranchId ? branchDetails.get(appState.selectedBranchId) ?? null : null;
}

export async function loadBranches() {
  try {
    const data = await getBranches();
    branches.clear();
    data.forEach((b) => branches.set(b.code, b));
    appState.lastError = null;
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    appState.lastError = message;
  }
}

export async function selectBranch(code: string) {
  appState.selectedBranchId = code;
  appState.zoomLevel = 'branch';

  if (!branchDetails.has(code)) {
    try {
      const detail = await getBranchDetail(code);
      branchDetails.set(code, detail);
      appState.lastError = null;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      appState.lastError = message;
    }
  }
}

export function deselectBranch() {
  appState.selectedBranchId = null;
  appState.zoomLevel = 'country';
}

/** Arc data for Deck.gl ArcLayer — connects each branch to the Central hub (Buenos Aires / SUC001). */
export interface ArcConnection {
  source: [number, number];
  target: [number, number];
  sourceBranch: BranchSummary;
  targetBranch: BranchSummary;
}

export function getArcData(): ArcConnection[] {
  const list = Array.from(branches.values());
  if (list.length === 0) return [];

  // Central hub: Buenos Aires branch (SUC001) or first available
  const central = list.find((b) => b.city === 'Buenos Aires') ?? list[0];
  const target: [number, number] = [central.coordinates.lng, central.coordinates.lat];

  return list
    .filter((b) => b.code !== central.code)
    .map((b) => ({
      source: [b.coordinates.lng, b.coordinates.lat] as [number, number],
      target,
      sourceBranch: b,
      targetBranch: central,
    }));
}
