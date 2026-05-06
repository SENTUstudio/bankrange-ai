<script lang="ts">
  export interface Props {
    title: string;
    rows: { label: string; value: string | number }[];
  }

  let { title, rows }: Props = $props();
</script>

<div class="border border-border bg-panel-sidebar p-4 rounded">
  <h3 class="text-brand-cyan text-sm font-bold uppercase tracking-wider mb-3 border-b border-border pb-2">
    {title}
  </h3>
  <div class="space-y-1.5">
    {#each rows as row}
      <div class="flex justify-between text-xs">
        <span class="text-content-secondary">{row.label}</span>
        <span class="text-content-primary font-mono">{row.value}</span>
      </div>
    {/each}
  </div>
</div>
