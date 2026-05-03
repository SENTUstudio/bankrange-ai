/** Topology types for the tactical map interface */

export interface Coordinates {
  x: number;
  y: number;
  lat: number;
  lng: number;
}

export interface BranchSummary {
  code: string;
  name: string;
  city: string;
  coordinates: Coordinates;
  workstation_count: number;
  employee_count: number;
  status: 'online' | 'degraded' | 'offline';
}

export interface NetworkSegment {
  name: string;
  cidr: string;
  vlan_id: number;
}

export interface Workstation {
  id: string;
  hostname: string;
  os_type: string;
  ip_address: string;
  eps: number;
}

export interface Employee {
  id: string;
  employee_code: string;
  full_name: string;
  department: string;
  workstation_id: string | null;
}

export interface BranchDetail {
  code: string;
  name: string;
  city: string;
  coordinates: Coordinates;
  segments: NetworkSegment[];
  workstations: Workstation[];
  employees: Employee[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'router' | 'switch' | 'workstation' | 'segment';
  x?: number;
  y?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: 'eth' | 'wifi' | 'vlan';
}

export interface NetworkGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
