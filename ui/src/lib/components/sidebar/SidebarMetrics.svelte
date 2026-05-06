<script lang="ts">
  import { engineState } from '$lib/state/engineStore.svelte';

  const eps = $derived(engineState.estimatedEPS);
  const ws = $derived(engineState.totalWorkstations);
  const connected = $derived(engineState.sseConnected);
</script>

<div class="flex flex-col gap-3">
  <div class="text-[10px] font-bold uppercase tracking-widest text-[var(--text-dim)] mb-1 px-3">
    Metrics
  </div>
  <div class="grid grid-cols-2 gap-2 px-3">
    <div class="border border-[var(--border-color)] rounded p-2">
      <div class="text-[10px] text-[var(--text-dim)] uppercase tracking-wider mb-1">Est. EPS</div>
      <div class="text-sm font-mono text-[var(--text-primary)]">{eps.toFixed(1)}</div>
    </div>
    <div class="border border-[var(--border-color)] rounded p-2">
      <div class="text-[10px] text-[var(--text-dim)] uppercase tracking-wider mb-1">Workstations</div>
      <div class="text-sm font-mono text-[var(--text-primary)]">{ws}</div>
    </div>
  </div>
  <div class="flex items-center gap-2 px-3">
    <div class="w-2 h-2 rounded-full" style="background: {connected ? 'var(--alert-green)' : 'var(--alert-red)'}; box-shadow: {connected ? 'var(--glow-green)' : 'var(--glow-red)'}"></div>
    <span class="text-[10px] font-mono uppercase tracking-wider" class:text-[var(--alert-green)]={connected} class:text-[var(--alert-red)]={!connected}>
      {connected ? 'Live' : 'Disconnected'}
    </span>
  </div>
</div>
