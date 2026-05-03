<script lang="ts">
  import type { GraphNode } from '$lib/types/topology';
  import { getNodeShape, getNodeColor, hexagonPoints, diamondPoints } from '$lib/utils/networkGraph';

  export interface Props {
    node: GraphNode & { x?: number; y?: number };
  }

  let { node }: Props = $props();

  const size = 12;

  let shape = $derived(getNodeShape(node.type));
  let color = $derived(getNodeColor(node.type));
</script>

<g transform="translate({node.x ?? 0}, {node.y ?? 0})">
  {#if shape === 'rect'}
    <rect x={-size} y={-size} width={size * 2} height={size * 2} fill={color} stroke="#000" stroke-width="1" />
  {:else if shape === 'polygon'}
    {#if node.type === 'segment'}
      <polygon points={hexagonPoints(0, 0, size)} fill={color} stroke="#000" stroke-width="1" />
    {:else}
      <polygon points={diamondPoints(0, 0, size)} fill={color} stroke="#000" stroke-width="1" />
    {/if}
  {:else if shape === 'circle'}
    <circle r={size} fill={color} stroke="#000" stroke-width="1" />
  {/if}

  <text y={size + 10} text-anchor="middle" fill="var(--color-text)" font-size="8" font-family="var(--font-mono)" class="pointer-events-none select-none" style="text-shadow: 0 1px 2px #000;">
    {node.label}
  </text>

  <title>{node.label} ({node.type})</title>
</g>
