<script>
  import '../app.css';
  import StatusBar from '$lib/components/StatusBar.svelte';
</script>

<StatusBar />
<div class="flex" style="margin-top: var(--status-bar-height); height: calc(100vh - var(--status-bar-height));">
  <slot />
</div>
