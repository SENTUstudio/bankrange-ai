import type { GraphNode } from '$lib/types/topology';

export type NodeShape = 'rect' | 'polygon' | 'circle';

export function getNodeShape(type: GraphNode['type']): NodeShape {
  switch (type) {
    case 'router':
      return 'rect';
    case 'switch':
    case 'segment':
      return 'polygon';
    case 'workstation':
      return 'circle';
    default:
      return 'circle';
  }
}

export function getNodeColor(type: GraphNode['type']): string {
  switch (type) {
    case 'router':
      return '#ffaa00';
    case 'switch':
      return '#00aaff';
    case 'workstation':
      return '#33ff33';
    case 'segment':
      return '#ff66cc';
    default:
      return '#888888';
  }
}

export function hexagonPoints(cx: number, cy: number, r: number): string {
  const points: string[] = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i - Math.PI / 6;
    points.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`);
  }
  return points.join(' ');
}

export function diamondPoints(cx: number, cy: number, r: number): string {
  return `${cx},${cy - r} ${cx + r},${cy} ${cx},${cy + r} ${cx - r},${cy}`;
}
