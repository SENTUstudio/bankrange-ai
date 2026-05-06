<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { MapboxOverlay } from '@deck.gl/mapbox';
  import { ScatterplotLayer, ArcLayer, TextLayer } from '@deck.gl/layers';
  import { branches, getArcData, selectBranch, deselectBranch } from '$lib/state/branchStore.svelte';
  import { getTextLayerCharacterSet } from '$lib/utils/deckgl-charset';
  import type { BranchSummary } from '$lib/types/topology';
  import type maplibregl from 'maplibre-gl';

  interface Props {
    mapInstance: maplibregl.Map;
  }

  let { mapInstance }: Props = $props();
  let overlay: MapboxOverlay | null = null;

  const STATUS_COLORS: Record<string, [number, number, number]> = {
    online: [0, 255, 136],
    degraded: [255, 136, 0],
    offline: [255, 51, 51],
  };

  function createLayers() {
    const list = Array.from(branches.values());
    const arcs = getArcData();
    const charset = getTextLayerCharacterSet();
    console.log('[DeckGlOverlay] createLayers called, branches:', list.length);
    console.log('[DeckGlOverlay] Cities:', list.map(b => b.city));
    console.log('[DeckGlOverlay] characterSet length:', charset.length);
    console.log('[DeckGlOverlay] characterSet includes ó:', charset.includes('ó'));
    console.log('[DeckGlOverlay] characterSet includes á:', charset.includes('á'));

    return [
      new ArcLayer<ReturnType<typeof getArcData>[number]>({
        id: 'arcs',
        data: arcs,
        getSourcePosition: (d) => d.source,
        getTargetPosition: (d) => d.target,
        getSourceColor: [0, 204, 255],
        getTargetColor: [0, 204, 255],
        getHeight: 0.5,
        getWidth: 2,
        pickable: false,
      }),
      new ScatterplotLayer<BranchSummary>({
        id: 'branches',
        data: list,
        pickable: true,
        opacity: 0.9,
        stroked: true,
        filled: true,
        radiusScale: 1,
        radiusMinPixels: 6,
        radiusMaxPixels: 50,
        lineWidthMinPixels: 1,
        getPosition: (d) => [d.coordinates.lng, d.coordinates.lat],
        getRadius: (d) => 10 + d.workstation_count / 2,
        getFillColor: (d) => STATUS_COLORS[d.status] ?? [128, 128, 128],
        getLineColor: [255, 255, 255],
        getLineWidth: 1,
        onClick: ({ object }) => {
          if (object) {
            selectBranch(object.code);
          }
        },
        onHover: ({ object }) => {
          if (mapInstance) {
            mapInstance.getCanvas().style.cursor = object ? 'pointer' : '';
          }
        },
      }),
      new TextLayer<BranchSummary>({
        id: 'labels',
        data: list,
        getPosition: (d) => [d.coordinates.lng, d.coordinates.lat],
        getText: (d) => d.city,
        getSize: 14,
        getColor: [224, 224, 224],
        getAngle: 0,
        getTextAnchor: 'middle',
        getAlignmentBaseline: 'center',
        getPixelOffset: [0, -20],
        pickable: false,
        fontFamily: '"JetBrains Mono", monospace',
        fontSettings: {
          sdf: false,
        },
        characterSet: charset,
        onDataLoad: () => console.log('[DeckGlOverlay] TextLayer data loaded'),
        onAfterRender: () => {
          // Check if text elements exist in deck canvas
          const canvas = document.querySelector('.deckgl-overlay canvas') || document.querySelector('canvas');
          if (canvas) {
            const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
            console.log('[DeckGlOverlay] Canvas size:', canvas.width, 'x', canvas.height);
            console.log('[DeckGlOverlay] WebGL context:', !!gl);
          }
          console.log('[DeckGlOverlay] Labels rendered for cities:', list.map(b => b.city));
        },
      }),
    ];
  }

  onMount(() => {
    if (!mapInstance) {
      console.log('[DeckGlOverlay] onMount skipped - no mapInstance');
      return;
    }

    console.log('[DeckGlOverlay] onMount starting, mapInstance:', !!mapInstance);

    // Font diagnostic: test if canvas can render accents with JetBrains Mono
    const canvas = document.createElement('canvas');
    canvas.width = 200; canvas.height = 50;
    const ctx = canvas.getContext('2d')!;
    ctx.font = '14px "JetBrains Mono", monospace';
    ctx.fillStyle = '#fff';
    ctx.fillText('Córdoba Tucumán', 10, 30);
    console.log('[DeckGlOverlay] Canvas font test - dataURL:', canvas.toDataURL().substring(0, 100));

    overlay = new MapboxOverlay({
      layers: [],
      interleaved: true,
      getTooltip: ({ object }) => {
        if (object && 'city' in object) {
          const b = object as BranchSummary;
          return {
            html: `<div style="padding:6px 10px;background:#111;border:1px solid #222;color:#e0e0e0;font-family:'JetBrains Mono',monospace;font-size:11px;border-radius:4px;pointer-events:none;">
              <strong style="color:var(--color-primary);">${b.city}</strong><br/>
              ${b.name}<br/>
              WS: ${b.workstation_count} | ${b.status.toUpperCase()}
            </div>`,
            style: { backgroundColor: 'transparent', boxShadow: 'none', padding: '0' },
          };
        }
        return null;
      },
      onClick: (info) => {
        if (!info.object) {
          deselectBranch();
        }
      },
    });

    mapInstance.addControl(overlay);
    const layers = createLayers();
    console.log('[DeckGlOverlay] Setting layers:', layers.map(l => l.id));
    overlay.setProps({ layers });
  });

  onDestroy(() => {
    if (overlay && mapInstance) {
      mapInstance.removeControl(overlay);
      overlay = null;
    }
  });

  $effect(() => {
    // Trigger reactivity on branch store mutations
    const _ = branches.size;
    if (overlay) {
      overlay.setProps({ layers: createLayers() });
    }
  });
</script>
