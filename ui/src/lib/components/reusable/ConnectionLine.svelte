<script lang="ts">
  export interface Props {
    source: { x?: number; y?: number };
    target: { x?: number; y?: number };
  }

  let { source, target }: Props = $props();

  let x1 = $derived(source.x ?? 0);
  let y1 = $derived(source.y ?? 0);
  let x2 = $derived(target.x ?? 0);
  let y2 = $derived(target.y ?? 0);
</script>

<line {x1} {y1} {x2} {y2} stroke="var(--color-border)" stroke-width="1.5" class="connection-line" />

<style>
  .connection-line {
    stroke-dasharray: 6 4;
    animation: dashFlow 1.5s linear infinite;
  }

  @keyframes dashFlow {
    from {
      stroke-dashoffset: 20;
    }
    to {
      stroke-dashoffset: 0;
    }
  }
</style>
