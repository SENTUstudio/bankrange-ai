import { describe, it, expect } from 'vitest';
import { runNetworkSimulation } from '$lib/state/networkGraphStore.svelte';
import type { GraphNode, GraphEdge } from '$lib/types/topology';

describe('networkGraphStore', () => {
  const nodes: GraphNode[] = [
    { id: 'r1', label: 'Router', type: 'router' },
    { id: 's1', label: 'Switch', type: 'switch' },
    { id: 's2', label: 'Switch', type: 'switch' },
    { id: 'ws1', label: 'WS1', type: 'workstation' },
    { id: 'ws2', label: 'WS2', type: 'workstation' },
    { id: 'seg1', label: 'Segment', type: 'segment' },
  ];

  const edges: GraphEdge[] = [
    { source: 'r1', target: 's1', type: 'eth' },
    { source: 'r1', target: 's2', type: 'eth' },
    { source: 's1', target: 'ws1', type: 'eth' },
    { source: 's2', target: 'ws2', type: 'eth' },
  ];

  it('should return nodes with settled x and y coordinates', () => {
    const result = runNetworkSimulation(nodes, edges, 200, 200);
    expect(result.nodes.length).toBe(nodes.length);
    for (const n of result.nodes) {
      expect(typeof n.x).toBe('number');
      expect(typeof n.y).toBe('number');
      expect(Number.isFinite(n.x)).toBe(true);
      expect(Number.isFinite(n.y)).toBe(true);
    }
  });

  it('should return edges with source and target references', () => {
    const result = runNetworkSimulation(nodes, edges, 200, 200);
    expect(result.edges.length).toBe(edges.length);
    for (const e of result.edges) {
      expect(typeof e.source).toBe('object');
      expect(typeof e.target).toBe('object');
    }
  });

  it('should produce deterministic output for identical inputs', () => {
    const r1 = runNetworkSimulation(nodes, edges, 300, 200);
    const r2 = runNetworkSimulation(nodes, edges, 300, 200);
    for (let i = 0; i < r1.nodes.length; i++) {
      expect(r1.nodes[i].x).toBeCloseTo(r2.nodes[i].x!, 5);
      expect(r1.nodes[i].y).toBeCloseTo(r2.nodes[i].y!, 5);
    }
  });

  it('should keep nodes within the given width and height', () => {
    const width = 400;
    const height = 300;
    const result = runNetworkSimulation(nodes, edges, width, height);
    for (const n of result.nodes) {
      expect(n.x!).toBeGreaterThanOrEqual(0);
      expect(n.x!).toBeLessThanOrEqual(width);
      expect(n.y!).toBeGreaterThanOrEqual(0);
      expect(n.y!).toBeLessThanOrEqual(height);
    }
  });
});
