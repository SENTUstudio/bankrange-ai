<script lang="ts">
  import { appState } from '$lib/state/appState.svelte';

  const bootLines = [
    '> Initializing BankRange Tactical Map...',
    '> Loading topology coordinates...',
    '> Establishing SSE uplink...',
    '> Synchronizing branch registry...',
    '> System ready.',
  ];

  let visibleLines = $state<string[]>([]);
  let progress = $state(0);
  let done = $state(false);
  let lineIndex = $state(0);

  function typeLine() {
    if (lineIndex >= bootLines.length) {
      done = true;
      setTimeout(() => {
        appState.phase = 'map';
      }, 600);
      return;
    }
    visibleLines = [...visibleLines, bootLines[lineIndex]];
    lineIndex++;
    progress = Math.min(100, (lineIndex / bootLines.length) * 100);
    setTimeout(typeLine, 400);
  }

  // Start typing on mount
  $effect(() => {
    const timer = setTimeout(typeLine, 200);
    // Auto-skip after 3s
    const autoSkip = setTimeout(() => {
      if (!done) {
        appState.phase = 'map';
      }
    }, 3000);
    return () => {
      clearTimeout(timer);
      clearTimeout(autoSkip);
    };
  });

  function skip() {
    appState.phase = 'map';
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div
  class="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[var(--color-bg)] cursor-pointer select-none"
  onclick={skip}
>
  <div class="w-full max-w-lg px-6">
    <div class="mb-4 text-[var(--color-success)] text-xs uppercase tracking-widest">
      BankRange OS v2.4.1
    </div>
    <div class="space-y-1 mb-6 min-h-[120px]">
      {#each visibleLines as line}
        <div class="text-[var(--color-text)] text-sm font-mono">{line}</div>
      {/each}
      {#if !done}
        <span class="inline-block w-2 h-4 bg-[var(--color-success)] animate-pulse"></span>
      {/if}
    </div>
    <div class="w-full h-1 bg-[var(--color-border)] rounded overflow-hidden">
      <div
        class="h-full bg-[var(--color-success)] transition-all duration-300"
        style="width: {progress}%"
      ></div>
    </div>
    <div class="mt-4 text-center text-[var(--color-muted)] text-xs">
      Click or press any key to skip
    </div>
  </div>
</div>
