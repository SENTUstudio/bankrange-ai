<script lang="ts">
  import { engineState } from '$lib/state/engineStore.svelte';

  const eps = $derived(engineState.estimatedEPS);
  const ws = $derived(engineState.totalWorkstations);
  const connected = $derived(engineState.sseConnected);
</script>

<div class="flex flex-col gap-3">
  <div class="text-[10px] font-bold uppercase tracking-widest text-content-dim mb-1 px-3">
    Metrics
  </div>
  <div class="grid grid-cols-2 gap-2 px-3">
    <div class="border border-border rounded p-2">
      <div class="text-[10px] text-content-dim uppercase tracking-wider mb-1">Est. EPS</div>
      <div class="text-sm font-mono text-content-primary">{eps.toFixed(1)}</div>
    </div>
    <div class="border border-border rounded p-2">
      <div class="text-[10px] text-content-dim uppercase tracking-wider mb-1">Workstations</div>
      <div class="text-sm font-mono text-content-primary">{ws}</div>
    </div>
  </div>
  <div class="flex items-center gap-2 px-3">
    <span
      class="w-2 h-2 rounded-full"
      class:bg-brand-green={connected}
      class:bg-brand-red={!connected}
    ></span>
    <span
      class="text-[10px] font-mono uppercase tracking-wider"
      class:text-brand-green={connected}
      class:text-brand-red={!connected}
    >
      {connected ? 'Live' : 'Disconnected'}
    </span>
  </div>
</div>
