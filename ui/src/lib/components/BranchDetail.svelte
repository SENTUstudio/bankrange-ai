<script lang="ts">
  import { getSelectedBranch, deselectBranch } from '$lib/state/branchStore.svelte';
  import { appState } from '$lib/state/appState.svelte';
  import DetailPanel from './reusable/DetailPanel.svelte';
  import NetworkGraph from './NetworkGraph.svelte';
  import type { BranchDetail as BranchDetailType } from '$lib/types/topology';

  let branch = $state<BranchDetailType | null>(null);

  // $effect properly tracks $state Map mutations (unlike $derived with async data)
  $effect(() => {
    branch = getSelectedBranch();
  });

  const isOpen = $derived(appState.zoomLevel === 'branch' && branch !== null);
</script>

<!-- Always rendered; visibility controlled by translate-x + overflow-hidden on parent -->
<div
  class="absolute top-0 right-0 bottom-0 z-30 w-96 border-l border-border bg-panel-sidebar backdrop-blur transition-transform duration-300 ease-in-out"
  class:translate-x-0={isOpen}
  class:translate-x-full={!isOpen}
>
  {#if isOpen && branch}
    <div class="p-4 h-full overflow-y-auto">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-brand-cyan text-sm font-bold uppercase tracking-wider">
          {branch.name}
        </h2>
        <button
          class="px-2 py-1 border border-border bg-panel-hover text-content-primary text-xs font-mono rounded hover:bg-border transition-colors"
          onclick={deselectBranch}
        >
          ← Back
        </button>
      </div>

      <div class="space-y-3 mb-4">
        <DetailPanel
          title="Branch Info"
          rows={[
            { label: 'Code', value: branch.code },
            { label: 'City', value: branch.city },
            { label: 'Segments', value: branch.segments.length },
            { label: 'Workstations', value: branch.workstations.length },
            { label: 'Employees', value: branch.employees.length },
          ]}
        />
      </div>

      <div class="border border-border bg-panel-sidebar rounded p-3">
        <h3 class="text-brand-cyan text-xs font-bold uppercase tracking-wider mb-2">
          Network Topology
        </h3>
        <NetworkGraph code={branch.code} width={340} height={240} />
      </div>
    </div>
  {/if}
</div>
