<script lang="ts">
  export interface Props {
    title: string;
    rows: { label: string; value: string | number }[];
  }

  let { title, rows }: Props = $props();
</script>

<div class="border border-[var(--color-border)] bg-[var(--color-panel)] p-4 rounded">
  <h3 class="text-[var(--color-primary)] text-sm font-bold uppercase tracking-wider mb-3 border-b border-[var(--color-border)] pb-2">
    {title}
  </h3>
  <div class="space-y-1.5">
    {#each rows as row}
      <div class="flex justify-between text-xs">
        <span class="text-[var(--color-muted)]">{row.label}</span>
        <span class="text-[var(--color-text)] font-mono">{row.value}</span>
      </div>
    {/each}
  </div>
</div>
