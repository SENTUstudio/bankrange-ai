<script lang="ts">
  export interface Props {
    level: 'info' | 'warn' | 'critical';
    text: string;
  }

  let { level, text }: Props = $props();

  const levelClasses: Record<string, string> = {
    info: 'bg-[var(--color-success)] text-black',
    warn: 'bg-[var(--color-warn)] text-black',
    critical: 'bg-[var(--color-alert)] text-white animate-pulse',
  };
</script>

<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider {levelClasses[level]}">
  {text}
</span>
