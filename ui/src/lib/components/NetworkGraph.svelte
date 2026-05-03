<script lang="ts">
  import { runNetworkSimulation } from '$lib/state/networkGraphStore.svelte';
  import { getBranchNetwork } from '$lib/services/api.service';
  import type { GraphNode, GraphEdge, NetworkGraph } from '$lib/types/topology';
  import NodeMarker from './reusable/NodeMarker.svelte';
  import ConnectionLine from './reusable/ConnectionLine.svelte';

  export interface Props {
    code: string;
    width?: number;
    height?: number;
  }

  let { code, width = 500, height = 300 }: Props = $props();

  let nodes = $state<GraphNode[]>([]);
  let edges = $state<GraphEdge[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);

  $effect(() => {
    let cancelled = false;
    loading = true;
    error = null;

    getBranchNetwork(code)
      .then((data: NetworkGraph) => {
        if (cancelled) return;
        const result = runNetworkSimulation(data.nodes, data.edges, width, height);
        nodes = result.nodes as GraphNode[];
        edges = result.edges as GraphEdge[];
        loading = false;
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        error = err instanceof Error ? err.message : String(err);
        loading = false;
      });

    return () => {
      cancelled = true;
    };
  });
</script>

<div class="relative w-full" style="height: {height}px;">
  {#if loading}
    <div class="absolute inset-0 flex items-center justify-center text-[var(--color-muted)] text-xs font-mono">
      LOADING NETWORK...
    </div>
  {:else if error}
    <div class="absolute inset-0 flex items-center justify-center text-[var(--color-alert)] text-xs font-mono">
      ERR: {error}
    </div>
  {:else}
    <svg {width} {height} class="w-full h-full">
      {#each edges as edge (edge.source + '-' + edge.target)}
        {@const src = nodes.find((n) => n.id === (edge.source as any).id || n.id === edge.source)}
        {@const tgt = nodes.find((n) => n.id === (edge.target as any).id || n.id === edge.target)}
        {#if src && tgt}
          <ConnectionLine source={src} target={tgt} />
        {/if}
      {/each}
      {#each nodes as node (node.id)}
        <NodeMarker {node} />
      {/each}
    </svg>
  {/if}
</div>
