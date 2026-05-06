<script lang="ts">
  import { engineState } from '$lib/state/engineStore.svelte';
  import AlertBadge from './reusable/AlertBadge.svelte';

  const statusConfig: Record<string, { level: 'info' | 'warn' | 'critical'; text: string }> = {
    running: { level: 'info', text: 'RUNNING' },
    stopped: { level: 'critical', text: 'STOPPED' },
  };

  let config = $derived(statusConfig[engineState.status] ?? { level: 'warn', text: 'UNKNOWN' });
</script>

<div class="fixed top-0 left-0 right-0 z-[100] h-12 flex items-center justify-between px-4 border-b border-[var(--color-border)] bg-[var(--color-bg)]/90 backdrop-blur">
  <div class="flex items-center gap-3">
    <span class="text-[var(--color-primary)] text-xs font-bold uppercase tracking-wider">BankRange</span>
    <AlertBadge level={config.level} text={config.text} />
    {#if !engineState.sseConnected}
      <AlertBadge level="critical" text="RECONNECTING..." />
    {/if}
  </div>

  <div class="flex items-center gap-4 text-xs font-mono">
    <div class="flex items-center gap-1.5">
      <span class="text-[var(--color-muted)]">EPS</span>
      <span class="text-[var(--color-text)]">{engineState.estimatedEPS.toFixed(1)}</span>
    </div>
    <div class="flex items-center gap-1.5">
      <span class="text-[var(--color-muted)]">WS</span>
      <span class="text-[var(--color-text)]">{engineState.totalWorkstations}</span>
    </div>
    <div class="flex items-center gap-1.5">
      <span class="text-[var(--color-muted)]">MULT</span>
      <span class="text-[var(--color-text)]">{engineState.multiplier.toFixed(1)}x</span>
    </div>
    <div class="w-2 h-2 rounded-full" class:bg-[var(--color-success)]={engineState.sseConnected} class:bg-[var(--color-alert)]={!engineState.sseConnected}></div>
  </div>
</div>
