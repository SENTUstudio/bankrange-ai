import { describe, it, expect, vi } from 'vitest';
import { engineState, updateEngineState, setMultiplier } from '$lib/state/engineStore.svelte';
import * as api from '$lib/services/api.service';
import { appState } from '$lib/state/appState.svelte';

vi.mock('$lib/services/api.service', () => ({
  postControl: vi.fn(),
}));

describe('engineStore', () => {
  it('should default to stopped state', () => {
    expect(engineState.status).toBe('stopped');
  });

  it('should default multiplier to 1.0', () => {
    expect(engineState.multiplier).toBe(1.0);
  });

  it('should update state from SSE payload', () => {
    updateEngineState({
      status: 'running',
      current_multiplier: 2.5,
      estimated_eps: 12.3,
      total_workstations: 100,
    });
    expect(engineState.status).toBe('running');
    expect(engineState.multiplier).toBe(2.5);
    expect(engineState.estimatedEPS).toBe(12.3);
    expect(engineState.totalWorkstations).toBe(100);
  });

  it('should call API on setMultiplier and update state', async () => {
    vi.mocked(api.postControl).mockResolvedValue({ message: 'OK', new_multiplier: 3.0 });
    await setMultiplier(3.0);
    expect(api.postControl).toHaveBeenCalledWith({ eps_multiplier: 3.0 });
    expect(engineState.multiplier).toBe(3.0);
    expect(appState.lastError).toBeNull();
  });

  it('should set lastError on API failure', async () => {
    vi.mocked(api.postControl).mockRejectedValue(new Error('Network down'));
    await expect(setMultiplier(5.0)).rejects.toThrow('Network down');
    expect(appState.lastError).toBe('Network down');
  });
});
