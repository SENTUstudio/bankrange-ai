import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mount } from 'svelte';
import DashboardSidebar from '$lib/components/DashboardSidebar.svelte';
import { branches } from '$lib/state/branchStore.svelte';
import { engineState } from '$lib/state/engineStore.svelte';
import { appState } from '$lib/state/appState.svelte';

function resetStores() {
  branches.clear();
  appState.selectedBranchId = null;
  appState.phase = 'boot';
  appState.zoomLevel = 'country';
  appState.mapReady = false;
  appState.lastError = null;
  engineState.status = 'stopped';
  engineState.multiplier = 1.0;
  engineState.estimatedEPS = 0;
  engineState.totalWorkstations = 0;
  engineState.sseConnected = true;
}

describe('DashboardSidebar', () => {
  let container: HTMLDivElement;

  beforeEach(() => {
    resetStores();
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
  });

  it('renders all 4 sub-components (check for section headings)', () => {
    mount(DashboardSidebar, { target: container });
    expect(container.textContent).toContain('Navigation');
    expect(container.textContent).toContain('Branches');
    expect(container.textContent).toContain('Metrics');
    expect(container.textContent).toContain('External');
  });

  it('has sidebar width from CSS class', () => {
    mount(DashboardSidebar, { target: container });
    const aside = container.querySelector('aside');
    expect(aside).not.toBeNull();
    expect(aside!.className).toContain('w-sidebar');
  });

  it('renders brand header "BankRange"', () => {
    mount(DashboardSidebar, { target: container });
    expect(container.textContent).toContain('BankRange');
  });

  it('renders footer "© 2026 BankRange AI"', () => {
    mount(DashboardSidebar, { target: container });
    expect(container.textContent).toContain('© 2026 BankRange AI');
  });

  it('renders as an aside element', () => {
    mount(DashboardSidebar, { target: container });
    const aside = container.querySelector('aside');
    expect(aside).not.toBeNull();
    expect(aside!.tagName).toBe('ASIDE');
  });
});
