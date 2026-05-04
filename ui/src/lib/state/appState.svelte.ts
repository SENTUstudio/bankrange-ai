/** Global UI state — Svelte 5 runes */

export type AppPhase = 'boot' | 'idle' | 'map';
export type ZoomLevel = 'country' | 'branch';

export const appState = $state<{
  phase: AppPhase;
  zoomLevel: ZoomLevel;
  selectedBranchId: string | null;
  mapReady: boolean;
  lastError: string | null;
}>({
  phase: 'boot',
  zoomLevel: 'country',
  selectedBranchId: null,
  mapReady: false,
  lastError: null,
});

export function setMapReady(ready: boolean) {
  appState.mapReady = ready;
}
