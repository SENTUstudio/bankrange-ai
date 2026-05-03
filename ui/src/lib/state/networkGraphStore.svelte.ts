import * as d3 from 'd3-force';
import type { GraphNode, GraphEdge } from '$lib/types/topology';

export interface SimulatedGraph {
  nodes: d3.SimulationNodeDatum[];
  edges: d3.SimulationLinkDatum<d3.SimulationNodeDatum>[];
}

export function runNetworkSimulation(
  nodes: GraphNode[],
  edges: GraphEdge[],
  width: number,
  height: number
): SimulatedGraph {
  // Deep copy to avoid mutating inputs
  const simNodes: d3.SimulationNodeDatum[] = nodes.map((n, i) => ({
    ...n,
    // Deterministic initial positions arranged in a circle
    x: width / 2 + Math.cos((i / nodes.length) * 2 * Math.PI) * (width * 0.25),
    y: height / 2 + Math.sin((i / nodes.length) * 2 * Math.PI) * (height * 0.25),
  }));

  const simEdges = edges.map((e) => ({ ...e }));

  const simulation = d3
    .forceSimulation(simNodes)
    .force(
      'link',
      d3
        .forceLink(simEdges)
        .id((d: any) => d.id)
        .distance(60)
    )
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('x', d3.forceX(width / 2).strength(0.05))
    .force('y', d3.forceY(height / 2).strength(0.05))
    .force(
      'collision',
      d3.forceCollide().radius((d: any) => (d.type === 'router' ? 25 : d.type === 'switch' ? 18 : 12))
    )
    .stop();

  // Deterministic 300 ticks
  for (let i = 0; i < 300; i++) {
    simulation.tick();
  }

  // Clamp positions within bounds
  for (const n of simNodes) {
    n.x = Math.max(10, Math.min(width - 10, n.x ?? width / 2));
    n.y = Math.max(10, Math.min(height - 10, n.y ?? height / 2));
  }

  return { nodes: simNodes, edges: simEdges };
}
