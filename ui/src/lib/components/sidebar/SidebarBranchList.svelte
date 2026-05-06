<script lang="ts">
  import { branches, selectBranch } from '$lib/state/branchStore.svelte';
  import { appState } from '$lib/state/appState.svelte';

  const branchList = $derived(Array.from(branches.values()));
  const isEmpty = $derived(branchList.length === 0);
</script>

<div class="flex flex-col min-h-0">
  <div class="text-[10px] font-bold uppercase tracking-widest text-[var(--text-dim)] mb-2 px-3">
    Branches
  </div>
  {#if isEmpty}
    <div class="px-3 py-4 text-xs font-mono text-[var(--text-dim)] border border-dashed border-[var(--border-color)] rounded">
      No branches registered.
    </div>
  {:else}
    <div class="flex flex-col gap-1 overflow-y-auto pr-1" style="max-height: 240px;">
      {#each branchList as branch (branch.code)}
        <button
          class="text-left px-3 py-2 rounded text-xs font-mono transition-colors border border-transparent
            {appState.selectedBranchId === branch.code
              ? 'text-[var(--cyan)] bg-[var(--cyan)]/10 border-[var(--cyan)]/20'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-panel-hover)]'}"
          onclick={() => selectBranch(branch.code)}
        >
          <div class="flex items-center justify-between">
            <span class="truncate">{branch.name}</span>
            <span class="text-[10px] text-[var(--text-dim)] ml-2 shrink-0">{branch.code}</span>
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>
