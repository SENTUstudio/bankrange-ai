import { describe, it, expect, vi } from 'vitest';
import { branches, branchDetails, getSelectedBranch, loadBranches, selectBranch, deselectBranch } from '$lib/state/branchStore.svelte';
import * as api from '$lib/services/api.service';
import { appState } from '$lib/state/appState.svelte';

vi.mock('$lib/services/api.service', () => ({
  getBranches: vi.fn(),
  getBranchDetail: vi.fn(),
}));

const mockBranch = {
  code: 'SUC001',
  name: 'Central',
  city: 'Buenos Aires',
  coordinates: { x: 620, y: 620, lat: -34.6, lng: -58.3 },
  workstation_count: 10,
  employee_count: 5,
  status: 'online' as const,
};

const mockDetail = {
  code: 'SUC001',
  name: 'Central',
  city: 'Buenos Aires',
  coordinates: { x: 620, y: 620, lat: -34.6, lng: -58.3 },
  segments: [],
  workstations: [],
  employees: [],
};

describe('branchStore', () => {
  it('should start with empty caches', () => {
    expect(branches.size).toBe(0);
    expect(branchDetails.size).toBe(0);
  });

  it('should load branches into cache', async () => {
    vi.mocked(api.getBranches).mockResolvedValue([mockBranch]);
    await loadBranches();
    expect(branches.has('SUC001')).toBe(true);
    expect(branches.get('SUC001')?.city).toBe('Buenos Aires');
  });

  it('should select a branch and fetch detail', async () => {
    vi.mocked(api.getBranchDetail).mockResolvedValue(mockDetail);
    await selectBranch('SUC001');
    expect(appState.selectedBranchId).toBe('SUC001');
    expect(appState.zoomLevel).toBe('branch');
    expect(branchDetails.has('SUC001')).toBe(true);
  });

  it('should derive selectedBranch', () => {
    expect(getSelectedBranch()?.code).toBe('SUC001');
  });

  it('should not refetch detail if already cached', async () => {
    const spy = vi.mocked(api.getBranchDetail);
    spy.mockClear();
    await selectBranch('SUC001');
    expect(spy).not.toHaveBeenCalled();
  });

  it('should deselect branch', () => {
    deselectBranch();
    expect(appState.selectedBranchId).toBeNull();
    expect(appState.zoomLevel).toBe('country');
  });

  it('should set lastError on load failure', async () => {
    vi.mocked(api.getBranches).mockRejectedValue(new Error('Timeout'));
    await loadBranches();
    expect(appState.lastError).toBe('Timeout');
  });
});
