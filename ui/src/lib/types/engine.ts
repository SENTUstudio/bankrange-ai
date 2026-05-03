/** Engine state types for SSE and control */

export interface EngineStatus {
  status: 'running' | 'stopped';
  current_multiplier: number;
  estimated_eps: number;
  total_workstations: number;
  timestamp?: string;
}

export interface ControlRequest {
  eps_multiplier: number;
}

export interface ControlResponse {
  message: string;
  new_multiplier: number;
}
