import { describe, it, expect } from 'vitest';
import { appState, resetMapTransform } from '$lib/state/appState.svelte';

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

  it('should reset map transform', () => {
    appState.mapTransform = { x: 100, y: 200, scale: 3 };
    resetMapTransform();
    expect(appState.mapTransform).toEqual({ x: 0, y: 0, scale: 1 });
  });
});
