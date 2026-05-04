<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { MapboxOverlay } from '@deck.gl/mapbox';
  import { ScatterplotLayer, ArcLayer, TextLayer } from '@deck.gl/layers';
  import { getMapContext } from 'svelte-maplibre-gl';
  import { branches, getArcData, selectBranch, deselectBranch } from '$lib/state/branchStore.svelte';
  import type { BranchSummary } from '$lib/types/topology';

  const mapCtx = getMapContext();
  let overlay: MapboxOverlay | null = null;

  const STATUS_COLORS: Record<string, [number, number, number]> = {
    online: [0, 255, 136],
    degraded: [255, 136, 0],
    offline: [255, 51, 51],
  };

  function createLayers() {
    const list = Array.from(branches.values());
    const arcs = getArcData();

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
          if (mapCtx.map) {
            mapCtx.map.getCanvas().style.cursor = object ? 'pointer' : '';
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
          sdf: true,
        },
      }),
    ];
  }

  onMount(() => {
    if (!mapCtx.map) return;

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

    mapCtx.map.addControl(overlay);
    overlay.setProps({ layers: createLayers() });
  });

  onDestroy(() => {
    if (overlay && mapCtx.map) {
      mapCtx.map.removeControl(overlay);
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
