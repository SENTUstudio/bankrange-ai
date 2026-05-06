<script lang="ts">
  import { engineState, setMultiplier } from '$lib/state/engineStore.svelte';
  import { appState } from '$lib/state/appState.svelte';

  let sliderVal = $state(engineState.multiplier);
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;

  function handleSliderChange(e: Event) {
    const val = parseFloat((e.target as HTMLInputElement).value);
    sliderVal = val;
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      setMultiplier(val).catch(() => {});
    }, 200);
  }

  async function toggleDeploy() {
    const target = engineState.status === 'running' ? 0 : sliderVal || 1;
    try {
      await setMultiplier(target);
    } catch {
      // Error already surfaces to appState.lastError
    }
  }
</script>

<div class="absolute bottom-4 right-4 z-[100] w-72 border border-[var(--color-border)] bg-[var(--color-panel)]/95 backdrop-blur rounded p-4">
  <div class="flex items-center justify-between mb-3">
    <h3 class="text-[var(--color-primary)] text-xs font-bold uppercase tracking-wider">Controls</h3>
    <span class="text-[10px] text-[var(--color-muted)] font-mono">v2.4</span>
  </div>

  <div class="flex items-center gap-3 mb-4">
    <button
      class="flex-1 py-2 rounded text-xs font-bold uppercase tracking-wider transition-colors
        {engineState.status === 'running'
          ? 'bg-[var(--color-alert)] text-white hover:bg-red-600'
          : 'bg-[var(--color-success)] text-black hover:bg-green-400'}"
      onclick={toggleDeploy}
    >
      {engineState.status === 'running' ? 'STOP' : 'DEPLOY'}
    </button>
  </div>

  <div class="mb-3">
    <div class="flex justify-between text-[10px] text-[var(--color-muted)] mb-1">
      <span>EPS Multiplier</span>
      <span class="font-mono text-[var(--color-text)]">{sliderVal.toFixed(1)}x</span>
    </div>
    <input
      type="range"
      min="0"
      max="10"
      step="0.1"
      value={sliderVal}
      oninput={handleSliderChange}
      class="w-full h-1 bg-[var(--color-border)] rounded-lg appearance-none cursor-pointer accent-[var(--color-primary)]"
    />
  </div>

  {#if appState.lastError}
    <div class="mt-3 text-[var(--color-alert)] text-[10px] font-mono truncate">
      ERR: {appState.lastError}
    </div>
  {/if}
</div>
