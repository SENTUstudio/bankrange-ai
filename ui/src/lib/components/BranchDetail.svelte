<script lang="ts">
  import { getSelectedBranch, deselectBranch } from '$lib/state/branchStore.svelte';
  import { appState } from '$lib/state/appState.svelte';
  import DetailPanel from './reusable/DetailPanel.svelte';
  import NetworkGraph from './NetworkGraph.svelte';

  const branch = $derived(getSelectedBranch());
  const isOpen = $derived(appState.zoomLevel === 'branch' && branch !== null);
</script>

{#if isOpen && branch}
  <div
    class="absolute top-0 right-0 bottom-0 z-30 w-96 border-l border-[var(--color-border)] bg-[var(--color-bg)]/95 backdrop-blur transform transition-transform duration-300 ease-in-out"
    class:translate-x-0={isOpen}
    class:translate-x-full={!isOpen}
  >
    <div class="p-4 h-full overflow-y-auto">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-[var(--color-primary)] text-sm font-bold uppercase tracking-wider">
          {branch.name}
        </h2>
        <button
          class="px-2 py-1 border border-[var(--color-border)] bg-[var(--color-panel)] text-[var(--color-text)] text-xs font-mono rounded hover:bg-[var(--color-border)] transition-colors"
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

      <div class="border border-[var(--color-border)] bg-[var(--color-panel)] rounded p-3">
        <h3 class="text-[var(--color-primary)] text-xs font-bold uppercase tracking-wider mb-2">
          Network Topology
        </h3>
        <NetworkGraph code={branch.code} width={340} height={240} />
      </div>
    </div>
  </div>
{/if}
