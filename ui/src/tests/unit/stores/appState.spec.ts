import { describe, it, expect } from 'vitest';
import { appState, setMapReady } from '$lib/state/appState.svelte';

describe('appState store', () => {
  it('should default to boot phase', () => {
    expect(appState.phase).toBe('boot');
  });

  it('should default zoomLevel to country', () => {
    expect(appState.zoomLevel).toBe('country');
  });

  it('should have null selectedBranchId', () => {
    expect(appState.selectedBranchId).toBeNull();
  });

  it('should default mapReady to false', () => {
    expect(appState.mapReady).toBe(false);
  });

  it('should set map ready', () => {
    setMapReady(true);
    expect(appState.mapReady).toBe(true);
    setMapReady(false);
    expect(appState.mapReady).toBe(false);
  });
});
