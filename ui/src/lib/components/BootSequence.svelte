<script lang="ts">
  import { appState } from '$lib/state/appState.svelte';

  const bootLines = [
    { text: '> INITIALIZING BANKRANGE TACTICAL MAP...', color: '#00ff88' },
    { text: '> LOADING TOPOLOGY COORDINATES...', color: '#00ccff' },
    { text: '> ESTABLISHING SECURE UPLINK...', color: '#00ccff' },
    { text: '> CONNECTING TO GRID: BUENOS AIRES...', color: '#00ccff' },
    { text: '> CONNECTING TO GRID: CORDOBA...', color: '#00ccff' },
    { text: '> CONNECTING TO GRID: ROSARIO...', color: '#00ccff' },
    { text: '> CONNECTING TO GRID: MENDOZA...', color: '#00ccff' },
    { text: '> CONNECTING TO GRID: TUCUMAN...', color: '#00ccff' },
    { text: '> CONNECTING TO GRID: LA PLATA...', color: '#00ccff' },
    { text: '> CONNECTING TO GRID: MAR DEL PLATA...', color: '#00ccff' },
    { text: '> CONNECTING TO GRID: SALTA...', color: '#00ccff' },
    { text: '> SYNCHRONIZING BRANCH REGISTRY...', color: '#00ccff' },
    { text: '> DECRYPTING TACTICAL DATA...', color: '#ff8800' },
    { text: '> SYSTEM READY.', color: '#00ff88' },
  ];

  let visibleLines = $state<{text: string; color: string}[]>([]);
  let progress = $state(0);
  let done = $state(false);
  let lineIndex = $state(0);
  let showGlitch = $state(false);

  function typeLine() {
    if (lineIndex >= bootLines.length) {
      done = true;
      setTimeout(() => {
        showGlitch = true;
        setTimeout(() => {
          appState.phase = 'map';
        }, 800);
      }, 400);
      return;
    }
    visibleLines = [...visibleLines, bootLines[lineIndex]];
    lineIndex++;
    progress = Math.min(100, (lineIndex / bootLines.length) * 100);
    setTimeout(typeLine, 250 + Math.random() * 200);
  }

  $effect(() => {
    const timer = setTimeout(typeLine, 500);
    return () => clearTimeout(timer);
  });

  function skip() {
    appState.phase = 'map';
  }
</script>

<svelte:window onkeydown={skip} />

<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div
  class="boot-overlay"
  class:glitch={showGlitch}
  onclick={skip}
>
  <!-- Scanlines -->
  <div class="scanlines"></div>
  
  <!-- Content -->
  <div class="boot-content">
    <div class="header">
      <div class="title">BANKRANGE TACTICAL CONSOLE</div>
      <div class="tagline">
        █▀ █▀▀ █▄░█ ▀█▀ █░█  ┎┤  Ingeniería de Datos &amp; Data Science  ├┒
      </div>
      <div class="tagline">
        ▄█ ██▄ █░▀█ ░█░ █▄█  ┖┤              en Python               ├┚
      </div>
      <div class="version">OS v2.4.1 // SECURE TERMINAL</div>
    </div>
    
    <div class="terminal">
      {#each visibleLines as line}
        <div class="line" style="color: {line.color}">{line.text}</div>
      {/each}
      {#if !done}
        <span class="cursor"></span>
      {/if}
    </div>
    
    <div class="progress-container">
      <div class="progress-bar">
        <div class="progress-fill" style="width: {progress}%"></div>
      </div>
      <div class="progress-text">{progress.toFixed(0)}%</div>
    </div>
    
    <div class="footer">[ CLICK OR PRESS ANY KEY TO SKIP ]</div>
  </div>
</div>

<style>
  .boot-overlay {
    position: fixed;
    inset: 0;
    z-index: 99999;
    background: #000;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Courier New', 'JetBrains Mono', monospace;
    cursor: pointer;
    user-select: none;
    transition: opacity 0.1s ease-out;
  }
  
  .boot-overlay.glitch {
    animation: glitchOut 0.8s ease-out forwards;
  }
  
  @keyframes glitchOut {
    0% { opacity: 1; filter: none; }
    20% { opacity: 1; filter: hue-rotate(90deg) saturate(200%); transform: translateX(2px); }
    40% { opacity: 0.8; filter: hue-rotate(180deg); transform: translateX(-2px); }
    60% { opacity: 0.6; filter: hue-rotate(270deg) saturate(300%); transform: translateX(3px); }
    80% { opacity: 0.3; filter: invert(1); }
    100% { opacity: 0; }
  }
  
  .scanlines {
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0, 255, 136, 0.03) 2px,
      rgba(0, 255, 136, 0.03) 4px
    );
    pointer-events: none;
    animation: scanlineMove 8s linear infinite;
  }
  
  @keyframes scanlineMove {
    0% { transform: translateY(0); }
    100% { transform: translateY(4px); }
  }
  
  .boot-content {
    width: 90%;
    max-width: 800px;
    padding: 2rem;
  }
  
  .header {
    text-align: center;
    margin-bottom: 3rem;
  }
  
  .title {
    color: #00ccff;
    font-size: 1.5rem;
    font-weight: bold;
    letter-spacing: 4px;
    text-shadow: 0 0 20px rgba(0, 204, 255, 0.5);
    margin-bottom: 0.5rem;
  }
  
  .version {
    color: #666;
    font-size: 0.75rem;
    letter-spacing: 2px;
    margin-top: 1rem;
  }
  
  .tagline {
    color: #00ff88;
    font-size: 0.65rem;
    font-family: 'Courier New', 'JetBrains Mono', monospace;
    letter-spacing: 1px;
    line-height: 1.6;
    text-shadow: 0 0 8px rgba(0, 255, 136, 0.3);
  }
  
  .terminal {
    min-height: 300px;
    margin-bottom: 2rem;
    font-size: 0.85rem;
    line-height: 1.8;
  }
  
  .line {
    animation: fadeIn 0.1s ease-out;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateX(-10px); }
    to { opacity: 1; transform: translateX(0); }
  }
  
  .cursor {
    display: inline-block;
    width: 8px;
    height: 16px;
    background: #00ff88;
    animation: blink 1s step-end infinite;
  }
  
  @keyframes blink {
    50% { opacity: 0; }
  }
  
  .progress-container {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
  }
  
  .progress-bar {
    flex: 1;
    height: 4px;
    background: #111;
    border: 1px solid #333;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #00ccff, #00ff88);
    box-shadow: 0 0 10px rgba(0, 204, 255, 0.5);
    transition: width 0.3s ease-out;
  }
  
  .progress-text {
    color: #00ff88;
    font-size: 0.75rem;
    width: 40px;
    text-align: right;
  }
  
  .footer {
    text-align: center;
    color: #333;
    font-size: 0.7rem;
    letter-spacing: 2px;
    animation: pulse 2s ease-in-out infinite;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 0.6; }
  }
</style>
