<script lang="ts">
  import SidebarNav from './sidebar/SidebarNav.svelte';
  import SidebarBranchList from './sidebar/SidebarBranchList.svelte';
  import SidebarMetrics from './sidebar/SidebarMetrics.svelte';
  import SidebarExternalLinks from './sidebar/SidebarExternalLinks.svelte';
</script>

<aside
  class="flex flex-col gap-6 shrink-0 w-sidebar border-r border-border bg-panel-sidebar overflow-y-auto"
>
  <div class="px-3 pt-4">
    <div class="text-xs font-bold uppercase tracking-widest text-brand-cyan mb-1">BankRange</div>
    <div class="text-[10px] font-mono text-content-dim">Tactical Console v2.4</div>
  </div>

  <SidebarNav />
  <SidebarBranchList />
  <SidebarMetrics />
  <SidebarExternalLinks />

  <div class="mt-auto px-3 pb-4">
    <div class="h-px bg-border mb-3"></div>
    <div class="text-[10px] font-mono text-content-dim">
      © 2026 BankRange AI
    </div>
  </div>
</aside>
