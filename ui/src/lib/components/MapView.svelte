<script lang="ts">
  import { onMount } from 'svelte';
  import maplibregl from 'maplibre-gl';
  import { appState } from '$lib/state/appState.svelte';
  import { branches, deselectBranch } from '$lib/state/branchStore.svelte';
  import DeckGlOverlay from './DeckGlOverlay.svelte';
  import 'maplibre-gl/dist/maplibre-gl.css';

  let mapContainer = $state<HTMLDivElement | null>(null);
  let mapInstance = $state<maplibregl.Map | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);

  onMount(() => {
    if (!mapContainer) return;

    try {
      const map = new maplibregl.Map({
        container: mapContainer,
        style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
        center: [-65, -38],
        zoom: 4,
        attributionControl: false,
      });

      map.on('load', () => {
        loading = false;
        mapInstance = map;
      });

      map.on('error', (e) => {
        console.error('Map error:', e);
        error = 'Failed to load map tiles';
        loading = false;
      });

      return () => {
        map.remove();
      };
    } catch (err) {
      console.error('Map init error:', err);
      error = err instanceof Error ? err.message : 'Unknown error';
      loading = false;
    }
  });

  // Fly to selected branch
  $effect(() => {
    if (mapInstance && appState.selectedBranchId) {
      const branch = branches.get(appState.selectedBranchId);
      if (branch) {
        mapInstance.flyTo({
          center: [branch.coordinates.lng, branch.coordinates.lat],
          zoom: 14,
          speed: 1.2,
        });
      }
    }
  });

  // Fly back to country view
  $effect(() => {
    if (mapInstance && !appState.selectedBranchId && appState.zoomLevel === 'country') {
      mapInstance.flyTo({
        center: [-65, -38],
        zoom: 4,
        speed: 1.2,
      });
    }
  });
</script>

<div class="absolute inset-0 z-0">
  <div bind:this={mapContainer} style="position: absolute; inset: 0; width: 100%; height: 100%;">
    {#if loading}
      <div class="absolute inset-0 flex items-center justify-center bg-[var(--bg-primary)]">
        <div class="flex flex-col items-center gap-3">
          <div class="w-8 h-8 border-2 border-[var(--cyan)] border-t-transparent rounded-full animate-spin"></div>
          <div class="text-[var(--cyan)] text-xs font-mono uppercase tracking-widest animate-pulse">
            Initializing tactical map...
          </div>
        </div>
      </div>
    {/if}
    {#if error}
      <div class="absolute inset-0 flex items-center justify-center bg-[var(--bg-primary)]">
        <div class="text-[var(--alert-red)] text-sm font-mono text-center p-4">
          <div class="mb-2">⚠ MAP ERROR</div>
          <div class="text-[var(--text-secondary)]">{error}</div>
        </div>
      </div>
    {/if}
  </div>

  {#if mapInstance}
    <DeckGlOverlay {mapInstance} />
  {/if}

  {#if appState.zoomLevel === 'branch'}
    <button
      class="absolute top-4 left-4 z-20 px-3 py-1 border border-[var(--border-color)] bg-[var(--bg-panel)] text-[var(--text-primary)] text-xs font-mono rounded hover:bg-[var(--border-color)] transition-colors"
      onclick={() => deselectBranch()}
    >
      ← Back to Country
    </button>
  {/if}
</div>
