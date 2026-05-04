<script lang="ts">
  import { onMount } from 'svelte';
  import maplibregl from 'maplibre-gl';
  import { appState, setMapReady } from '$lib/state/appState.svelte';
  import { branches, deselectBranch } from '$lib/state/branchStore.svelte';
  import 'maplibre-gl/dist/maplibre-gl.css';

  let MapLibre = $state<any>(null);
  let DeckGlOverlay = $state<any>(null);
  let loading = $state(true);
  let mapInstance = $state<maplibregl.Map | undefined>(undefined);
  let mapVisible = $state(false);

  onMount(async () => {
    const [maplibreMod, overlayMod] = await Promise.all([
      import('svelte-maplibre-gl'),
      import('$lib/components/DeckGlOverlay.svelte'),
    ]);
    MapLibre = maplibreMod.MapLibre;
    DeckGlOverlay = overlayMod.default;
    loading = false;
    setMapReady(true);
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
          curve: 1.2,
          essential: true,
        });
      }
    }
  });

  // Fly back to country view on deselect
  $effect(() => {
    if (mapInstance && !appState.selectedBranchId && appState.zoomLevel === 'country') {
      const center = mapInstance.getCenter();
      const zoom = mapInstance.getZoom();
      const targetLng = -65;
      const targetLat = -38;
      const targetZoom = 4;
      const dist = Math.sqrt(
        Math.pow(center.lng - targetLng, 2) + Math.pow(center.lat - targetLat, 2)
      );
      if (dist > 0.5 || Math.abs(zoom - targetZoom) > 0.5) {
        mapInstance.flyTo({
          center: [targetLng, targetLat],
          zoom: targetZoom,
          speed: 1.2,
          curve: 1.2,
          essential: true,
        });
      }
    }
  });
</script>

<div class="fixed top-10 left-0 right-0 bottom-0 z-0 bg-[var(--color-bg)]">
  {#if loading || !MapLibre}
    <div class="absolute inset-0 flex items-center justify-center">
      <div class="flex flex-col items-center gap-3">
        <div class="w-8 h-8 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin"></div>
        <div class="text-[var(--color-primary)] text-xs font-mono uppercase tracking-widest animate-pulse">
          Initializing tactical map...
        </div>
      </div>
    </div>
  {:else}
    <div
      class="w-full h-full transition-opacity duration-700 ease-out"
      class:opacity-0={!mapVisible}
      class:opacity-100={mapVisible}
    >
      <MapLibre
        class="w-full h-full"
        style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
        center={[-65, -38]}
        zoom={4}
        autoloadGlobalCss={false}
        bind:map={mapInstance}
        onload={() => {
          mapVisible = true;
        }}
      >
        <DeckGlOverlay />
      </MapLibre>
    </div>
  {/if}

  {#if appState.zoomLevel === 'branch'}
    <button
      class="absolute top-4 left-4 z-20 px-3 py-1 border border-[var(--color-border)] bg-[var(--color-panel)] text-[var(--color-text)] text-xs font-mono rounded hover:bg-[var(--color-border)] transition-colors"
      onclick={() => deselectBranch()}
    >
      ← Back to Country
    </button>
  {/if}
</div>
