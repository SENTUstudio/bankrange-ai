<script>
  import '../app.css';
  import StatusBar from '$lib/components/StatusBar.svelte';
</script>

<StatusBar />
<div class="flex mt-status-bar h-[calc(100vh-var(--status-bar-height))]">
  <slot />
</div>
