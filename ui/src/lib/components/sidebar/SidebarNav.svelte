<script lang="ts">
  const navItems = [
    { label: 'Dashboard', href: '/', active: true },
    { label: 'Logs', href: '/logs', active: false },
    { label: 'Settings', href: '/settings', active: false },
  ];
</script>

<nav class="flex flex-col gap-1">
  <div class="text-[10px] font-bold uppercase tracking-widest text-[var(--text-dim)] mb-2 px-3">
    Navigation
  </div>
  {#each navItems as item}
    <a
      href={item.href}
      target="_self"
      class="px-3 py-2 rounded text-xs font-mono uppercase tracking-wider transition-colors
        {item.active
          ? 'text-[var(--cyan)] bg-[var(--cyan)]/10 border border-[var(--cyan)]/20'
          : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-panel-hover)]'}"
    >
      {item.label}
    </a>
  {/each}
</nav>
