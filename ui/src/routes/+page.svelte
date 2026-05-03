<script>
  import { appState } from '$lib/state/appState.svelte';
  import { engineState, updateEngineState } from '$lib/state/engineStore.svelte';
  import { loadBranches } from '$lib/state/branchStore.svelte';
  import { sseService } from '$lib/services/sse.service';
  import BootSequence from '$lib/components/BootSequence.svelte';
  import MapView from '$lib/components/MapView.svelte';
  import ControlPanel from '$lib/components/ControlPanel.svelte';
  import { onMount } from 'svelte';

  let sseConnected = $state(true);

  onMount(() => {
    loadBranches();
    sseService.connect(
      (data) => {
        updateEngineState(data);
      },
      (connected) => {
        sseConnected = connected;
      }
    );
    return () => {
      sseService.disconnect();
    };
  });
</script>

{#if appState.phase === 'boot'}
  <BootSequence />
{:else}
  <MapView />
  <ControlPanel />
{/if}
