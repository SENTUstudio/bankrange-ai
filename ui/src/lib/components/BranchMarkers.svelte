<script lang="ts">
  import { branches } from '$lib/state/branchStore.svelte';

  export interface Props {
    onSelect: (code: string) => void;
  }

  let { onSelect }: Props = $props();

  const statusColors: Record<string, string> = {
    online: '#33ff33',
    degraded: '#ffaa00',
    offline: '#ff3333',
  };
</script>

<g>
  {#each branches.values() as branch (branch.code)}
    {@const color = statusColors[branch.status] || '#888888'}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <g
      class="cursor-pointer"
      transform="translate({branch.coordinates.x}, {branch.coordinates.y})"
      onclick={() => onSelect(branch.code)}
      role="button"
      tabindex="0"
      aria-label="Branch {branch.name}"
    >
      {#if branch.status === 'offline'}
        <circle r="10" fill="none" stroke={color} stroke-width="1" opacity="0.6">
          <animate attributeName="r" values="8;14;8" dur="2s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.6;0;0.6" dur="2s" repeatCount="indefinite" />
        </circle>
      {/if}
      <circle r="5" fill={color} stroke="#000" stroke-width="1" />
      <text
        y="-10"
        text-anchor="middle"
        fill="var(--color-text)"
        font-size="8"
        font-family="var(--font-mono)"
        class="pointer-events-none select-none"
        style="text-shadow: 0 1px 2px #000;"
      >
        {branch.city}
      </text>
      <title>{branch.name} — {branch.workstation_count} WS, {branch.employee_count} EMP</title>
    </g>
  {/each}
</g>
