import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mount } from 'svelte';
import SidebarBranchList from '$lib/components/sidebar/SidebarBranchList.svelte';
import { branches, selectBranch } from '$lib/state/branchStore.svelte';
import { appState } from '$lib/state/appState.svelte';

function resetStores() {
  branches.clear();
  appState.selectedBranchId = null;
  appState.phase = 'boot';
  appState.zoomLevel = 'country';
  appState.mapReady = false;
  appState.lastError = null;
}

describe('SidebarBranchList', () => {
  let container: HTMLDivElement;

  beforeEach(() => {
    resetStores();
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
  });

  it('renders branch items when branches are populated', () => {
    branches.set('SUC001', {
      code: 'SUC001',
      name: 'Casa Central',
      city: 'Buenos Aires',
      coordinates: { x: 0, y: 0, lat: -34.6, lng: -58.4 },
      workstation_count: 100,
      employee_count: 150,
      status: 'online',
    });
    branches.set('SUC002', {
      code: 'SUC002',
      name: 'Sucursal Norte',
      city: 'Córdoba',
      coordinates: { x: 10, y: 10, lat: -31.4, lng: -64.2 },
      workstation_count: 50,
      employee_count: 75,
      status: 'online',
    });

    mount(SidebarBranchList, { target: container });
    const buttons = container.querySelectorAll('button');
    expect(buttons).toHaveLength(2);
    expect(container.textContent).toContain('Casa Central');
    expect(container.textContent).toContain('Sucursal Norte');
  });

  it('shows empty state when no branches', () => {
    mount(SidebarBranchList, { target: container });
    expect(container.textContent).toContain('No branches registered.');
    expect(container.querySelectorAll('button')).toHaveLength(0);
  });

  it('selected branch has active class (cyan border)', () => {
    branches.set('SUC001', {
      code: 'SUC001',
      name: 'Casa Central',
      city: 'Buenos Aires',
      coordinates: { x: 0, y: 0, lat: -34.6, lng: -58.4 },
      workstation_count: 100,
      employee_count: 150,
      status: 'online',
    });
    appState.selectedBranchId = 'SUC001';

    mount(SidebarBranchList, { target: container });
    const buttons = container.querySelectorAll('button');
    expect(buttons[0].className).toContain('border-brand-cyan-20');
  });

  it('clicking a branch calls selectBranch (or updates selectedBranchId)', () => {
    branches.set('SUC001', {
      code: 'SUC001',
      name: 'Casa Central',
      city: 'Buenos Aires',
      coordinates: { x: 0, y: 0, lat: -34.6, lng: -58.4 },
      workstation_count: 100,
      employee_count: 150,
      status: 'online',
    });

    mount(SidebarBranchList, { target: container });
    const button = container.querySelector('button');
    expect(button).not.toBeNull();
    button!.click();
    expect(appState.selectedBranchId).toBe('SUC001');
    expect(appState.zoomLevel).toBe('branch');
  });

  it('section heading "Branches" is rendered', () => {
    mount(SidebarBranchList, { target: container });
    expect(container.textContent).toContain('Branches');
  });
});
