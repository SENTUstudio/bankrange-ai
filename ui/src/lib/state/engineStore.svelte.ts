import { postControl } from '$lib/services/api.service';
import type { EngineStatus } from '$lib/types/engine';
import { appState } from './appState.svelte';

export const engineState = $state<{
  status: 'running' | 'stopped';
  multiplier: number;
  estimatedEPS: number;
  totalWorkstations: number;
}>({
  status: 'stopped',
  multiplier: 1.0,
  estimatedEPS: 0,
  totalWorkstations: 0,
});

export function updateEngineState(payload: EngineStatus) {
  engineState.status = payload.status;
  engineState.multiplier = payload.current_multiplier;
  engineState.estimatedEPS = payload.estimated_eps;
  engineState.totalWorkstations = payload.total_workstations;
}

export async function setMultiplier(val: number) {
  try {
    await postControl({ eps_multiplier: val });
    engineState.multiplier = val;
    appState.lastError = null;
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    appState.lastError = message;
    throw err;
  }
}
