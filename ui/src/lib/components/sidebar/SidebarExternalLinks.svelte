<script lang="ts">
  const links = [
    { label: 'Grafana', href: 'http://localhost:3000' },
    { label: 'Kafka UI', href: 'http://localhost:8081' },
    { label: 'API Docs', href: 'http://localhost:8000/docs' },
  ];
</script>

<div class="flex flex-col gap-1">
  <div class="text-[10px] font-bold uppercase tracking-widest text-[var(--text-dim)] mb-2 px-3">
    External
  </div>
  {#each links as link}
    <a
      href={link.href}
      target="_blank"
      rel="noopener noreferrer"
      class="px-3 py-2 rounded text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--cyan)] hover:bg-[var(--bg-panel-hover)] transition-colors flex items-center justify-between"
    >
      <span>{link.label}</span>
      <span class="text-[10px] text-[var(--text-dim)]">↗</span>
    </a>
  {/each}
</div>
