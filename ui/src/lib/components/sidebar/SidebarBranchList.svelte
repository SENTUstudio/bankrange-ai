<script lang="ts">
  import { branches, selectBranch } from '$lib/state/branchStore.svelte';
  import { appState } from '$lib/state/appState.svelte';

  const branchList = $derived(Array.from(branches.values()));
  const isEmpty = $derived(branchList.length === 0);
</script>

<div class="flex flex-col min-h-0">
  <div class="text-[10px] font-bold uppercase tracking-widest text-content-dim mb-2 px-3">
    Branches
  </div>
  {#if isEmpty}
    <div class="px-3 py-4 text-xs font-mono text-content-dim border border-dashed border-border rounded">
      No branches registered.
    </div>
  {:else}
    <div class="flex flex-col gap-1 overflow-y-auto pr-1 max-h-60">
      {#each branchList as branch (branch.code)}
        <button
          class="text-left px-3 py-2 rounded text-xs font-mono transition-colors border border-transparent
            {appState.selectedBranchId === branch.code
              ? 'text-brand-cyan bg-brand-cyan-10 border-brand-cyan-20'
              : 'text-content-secondary hover:text-content-primary hover:bg-panel-hover'}"
          onclick={() => selectBranch(branch.code)}
        >
          <div class="flex items-center justify-between">
            <span class="truncate">{branch.name}</span>
            <span class="text-[10px] text-content-dim ml-2 shrink-0">{branch.code}</span>
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>
