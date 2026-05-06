<script>
  import { appState } from '$lib/state/appState.svelte';
  import { updateEngineState } from '$lib/state/engineStore.svelte';
  import { loadBranches } from '$lib/state/branchStore.svelte';
  import { sseService } from '$lib/services/sse.service';
  import BootSequence from '$lib/components/BootSequence.svelte';
  import DashboardSidebar from '$lib/components/DashboardSidebar.svelte';
  import MapView from '$lib/components/MapView.svelte';
  import ControlPanel from '$lib/components/ControlPanel.svelte';
  import BranchDetail from '$lib/components/BranchDetail.svelte';
  import { onMount } from 'svelte';

  onMount(() => {
    loadBranches();
    sseService.connect();
    return () => {
      sseService.disconnect();
    };
  });
</script>

{#if appState.phase === 'boot'}
  <BootSequence />
{:else}
  <DashboardSidebar />
  <div class="relative flex-1 min-w-0 overflow-hidden">
    <MapView />
    <ControlPanel />
    <BranchDetail />
  </div>
{/if}
