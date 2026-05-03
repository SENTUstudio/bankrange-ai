/** Global UI state — Svelte 5 runes */

export type AppPhase = 'boot' | 'idle' | 'map';
export type ZoomLevel = 'country' | 'branch';

export interface MapTransform {
  x: number;
  y: number;
  scale: number;
}

export const appState = $state<{
  phase: AppPhase;
  zoomLevel: ZoomLevel;
  selectedBranchId: string | null;
  mapTransform: MapTransform;
  lastError: string | null;
}>({
  phase: 'boot',
  zoomLevel: 'country',
  selectedBranchId: null,
  mapTransform: { x: 0, y: 0, scale: 1 },
  lastError: null,
});

export function resetMapTransform() {
  appState.mapTransform = { x: 0, y: 0, scale: 1 };
}
