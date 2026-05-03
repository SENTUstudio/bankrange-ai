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
