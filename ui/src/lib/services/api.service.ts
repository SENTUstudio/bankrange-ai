import type { BranchSummary, BranchDetail, NetworkGraph } from '$lib/types/topology';
import type { EngineStatus, ControlRequest, ControlResponse } from '$lib/types/engine';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function _fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    ...options,
  });

  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      message = body.detail || body.message || message;
    } catch {
      /* ignore parse error */
    }
    throw new ApiError(res.status, message);
  }

  return res.json() as Promise<T>;
}

export async function getStatus(): Promise<EngineStatus> {
  return _fetchJson<EngineStatus>('/status');
}

export async function postControl(req: ControlRequest): Promise<ControlResponse> {
  return _fetchJson<ControlResponse>('/control', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function getBranches(): Promise<BranchSummary[]> {
  return _fetchJson<BranchSummary[]>('/topology/branches');
}

export async function getBranchDetail(code: string): Promise<BranchDetail> {
  return _fetchJson<BranchDetail>(`/topology/branches/${encodeURIComponent(code)}`);
}

export async function getBranchNetwork(code: string): Promise<NetworkGraph> {
  return _fetchJson<NetworkGraph>(`/topology/branches/${encodeURIComponent(code)}/network`);
}

export { ApiError };
