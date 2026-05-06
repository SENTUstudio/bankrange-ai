<script lang="ts">
  import SidebarNav from './sidebar/SidebarNav.svelte';
  import SidebarBranchList from './sidebar/SidebarBranchList.svelte';
  import SidebarMetrics from './sidebar/SidebarMetrics.svelte';
  import SidebarExternalLinks from './sidebar/SidebarExternalLinks.svelte';
</script>

<aside
  class="flex flex-col gap-6 shrink-0 border-r border-[var(--border-color)] bg-[var(--bg-panel)] overflow-y-auto isolate"
  style="width: var(--sidebar-width);"
>
  <div class="px-3 pt-4">
    <div class="text-xs font-bold uppercase tracking-widest text-[var(--cyan)] mb-1">BankRange</div>
    <div class="text-[10px] font-mono text-[var(--text-dim)]">Tactical Console v2.4</div>
  </div>

  <SidebarNav />
  <SidebarBranchList />
  <SidebarMetrics />
  <SidebarExternalLinks />

  <div class="mt-auto px-3 pb-4">
    <div class="h-px bg-[var(--border-color)] mb-3"></div>
    <div class="text-[10px] font-mono text-[var(--text-dim)]">
      © 2026 BankRange AI
    </div>
  </div>
</aside>
