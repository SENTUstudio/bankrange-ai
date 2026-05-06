import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mount } from 'svelte';
import SidebarMetrics from '$lib/components/sidebar/SidebarMetrics.svelte';
import { engineState } from '$lib/state/engineStore.svelte';

function resetEngineState() {
  engineState.status = 'stopped';
  engineState.multiplier = 1.0;
  engineState.estimatedEPS = 0;
  engineState.totalWorkstations = 0;
  engineState.sseConnected = true;
}

describe('SidebarMetrics', () => {
  let container: HTMLDivElement;

  beforeEach(() => {
    resetEngineState();
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
  });

  it('displays estimated EPS with correct formatting', () => {
    engineState.estimatedEPS = 1234.5;
    mount(SidebarMetrics, { target: container });
    expect(container.textContent).toContain('1234.5');
  });

  it('displays total workstations count', () => {
    engineState.totalWorkstations = 2000;
    mount(SidebarMetrics, { target: container });
    expect(container.textContent).toContain('2000');
  });

  it('shows "Live" with green dot when connected', () => {
    engineState.sseConnected = true;
    mount(SidebarMetrics, { target: container });
    expect(container.textContent).toContain('Live');
  });

  it('shows "Disconnected" with red dot when not connected', () => {
    engineState.sseConnected = false;
    mount(SidebarMetrics, { target: container });
    expect(container.textContent).toContain('Disconnected');
  });

  it('section heading "Metrics" is rendered', () => {
    mount(SidebarMetrics, { target: container });
    expect(container.textContent).toContain('Metrics');
  });
});
