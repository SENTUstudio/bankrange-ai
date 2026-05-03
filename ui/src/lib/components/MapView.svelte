<script lang="ts">
  import { appState, resetMapTransform } from '$lib/state/appState.svelte';
  import { branches, selectBranch, deselectBranch } from '$lib/state/branchStore.svelte';
  import ArgentinaMap from './ArgentinaMap.svelte';
  import BranchMarkers from './BranchMarkers.svelte';

  let svgRef = $state<SVGSVGElement | null>(null);
  let isDragging = $state(false);
  let dragStart = $state({ x: 0, y: 0 });

  function onWheel(e: WheelEvent) {
    e.preventDefault();
    const scaleFactor = e.deltaY > 0 ? 0.9 : 1.1;
    const newScale = Math.max(0.5, Math.min(8, appState.mapTransform.scale * scaleFactor));
    appState.mapTransform = {
      ...appState.mapTransform,
      scale: newScale,
    };
  }

  function onPointerDown(e: PointerEvent) {
    if (e.button !== 0) return;
    isDragging = true;
    dragStart = { x: e.clientX, y: e.clientY };
    (e.target as Element)?.setPointerCapture?.(e.pointerId);
  }

  function onPointerMove(e: PointerEvent) {
    if (!isDragging) return;
    const dx = e.clientX - dragStart.x;
    const dy = e.clientY - dragStart.y;
    dragStart = { x: e.clientX, y: e.clientY };
    appState.mapTransform = {
      x: appState.mapTransform.x + dx,
      y: appState.mapTransform.y + dy,
      scale: appState.mapTransform.scale,
    };
  }

  function onPointerUp() {
    isDragging = false;
  }

  function onBackgroundClick() {
    if (appState.zoomLevel === 'branch') {
      deselectBranch();
      resetMapTransform();
    }
  }

  // When zoomLevel changes to branch, animate scale
  $effect(() => {
    if (appState.zoomLevel === 'branch' && appState.selectedBranchId) {
      const branch = branches.get(appState.selectedBranchId);
      if (branch) {
        // Center on branch coordinate
        const targetScale = 4;
        const cx = branch.coordinates.x;
        const cy = branch.coordinates.y;
        // Compute translate to center the branch in viewport
        // Assuming viewport center is roughly 500,400 for viewBox 1000x800
        const tx = 500 - cx * targetScale;
        const ty = 400 - cy * targetScale;
        appState.mapTransform = { x: tx, y: ty, scale: targetScale };
      }
    } else if (appState.zoomLevel === 'country') {
      resetMapTransform();
    }
  });
</script>

<div class="fixed inset-0 pt-10 pb-0 overflow-hidden bg-[var(--color-bg)]">
  <svg
    bind:this={svgRef}
    class="w-full h-full cursor-grab active:cursor-grabbing"
    viewBox="0 0 1000 800"
    onwheel={onWheel}
    onpointerdown={onPointerDown}
    onpointermove={onPointerMove}
    onpointerup={onPointerUp}
    onpointerleave={onPointerUp}
    role="img"
    aria-label="Tactical map of Argentina"
  >
    <g
      style="transform: translate({appState.mapTransform.x}px, {appState.mapTransform.y}px) scale({appState.mapTransform.scale}); transition: transform 400ms ease-in-out; transform-origin: center;"
    >
      <ArgentinaMap />
      <BranchMarkers onSelect={selectBranch} />
    </g>
  </svg>

  <!-- Click outside to deselect -->
  {#if appState.zoomLevel === 'branch'}
    <button
      class="absolute top-12 left-4 z-20 px-3 py-1 border border-[var(--color-border)] bg-[var(--color-panel)] text-[var(--color-text)] text-xs font-mono rounded hover:bg-[var(--color-border)] transition-colors"
      onclick={onBackgroundClick}
    >
      ← Back to Country
    </button>
  {/if}
</div>
