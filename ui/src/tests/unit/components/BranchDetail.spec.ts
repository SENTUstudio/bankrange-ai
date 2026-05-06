import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount } from 'svelte';
import BranchDetail from '$lib/components/BranchDetail.svelte';
import { branchDetails } from '$lib/state/branchStore.svelte';
import { appState } from '$lib/state/appState.svelte';
import * as api from '$lib/services/api.service';

vi.mock('$lib/services/api.service', () => ({
  getBranchNetwork: vi.fn(),
}));

vi.mock('$lib/components/NetworkGraph.svelte', () => ({
  default: (() => ({})) as any,
}));

vi.mock('$lib/components/reusable/DetailPanel.svelte', () => ({
  default: (() => ({})) as any,
}));

function resetStores() {
  branchDetails.clear();
  appState.selectedBranchId = null;
  appState.zoomLevel = 'country';
  appState.phase = 'boot';
  appState.mapReady = false;
  appState.lastError = null;
}

describe('BranchDetail', () => {
  let container: HTMLDivElement;

  beforeEach(() => {
    resetStores();
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
  });

  it('shows branch details when details are loaded after mount', async () => {
    vi.mocked(api.getBranchNetwork).mockResolvedValue({ nodes: [], edges: [] });

    // Set selection but NO details yet (simulates async fetch pending)
    appState.selectedBranchId = 'SUC001';
    appState.zoomLevel = 'branch';

    mount(BranchDetail, { target: container });

    // Panel should be hidden because no details yet
    expect(container.textContent).not.toContain('Casa Central');

    // Simulate async fetch completing
    branchDetails.set('SUC001', {
      code: 'SUC001',
      name: 'Casa Central',
      city: 'Buenos Aires',
      coordinates: { x: 0, y: 0, lat: -34.6, lng: -58.4 },
      segments: [],
      workstations: [],
      employees: [],
    });

    // Allow reactivity to tick
    await new Promise((r) => setTimeout(r, 10));

    // Panel should now show the branch details
    expect(container.textContent).toContain('Casa Central');
    expect(container.textContent).toContain('← Back');
  });

  it('hides panel when no branch is selected', () => {
    mount(BranchDetail, { target: container });
    const div = container.querySelector('div');
    expect(div).not.toBeNull();
    expect(div!.className).toContain('translate-x-full');
  });
});
