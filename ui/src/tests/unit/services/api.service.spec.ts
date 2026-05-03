import { describe, it, expect, vi, afterEach } from 'vitest';
import { getBranches, getBranchDetail, getBranchNetwork, postControl, getStatus, ApiError } from '$lib/services/api.service';

describe('api.service', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('getStatus should fetch /status', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'running', current_multiplier: 1, estimated_eps: 5, total_workstations: 10 }),
    } as Response);

    const res = await getStatus();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/status'),
      expect.objectContaining({ headers: expect.objectContaining({ 'Content-Type': 'application/json' }) })
    );
    expect(res.status).toBe('running');
  });

  it('getBranches should return typed array', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [{ code: 'SUC001', name: 'Test', city: 'BA', coordinates: { x: 0, y: 0, lat: 0, lng: 0 }, workstation_count: 1, employee_count: 1, status: 'online' }],
    } as Response);

    const res = await getBranches();
    expect(res[0].code).toBe('SUC001');
  });

  it('should throw ApiError on 404', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Not found' }),
    } as Response);

    await expect(getBranchDetail('BAD')).rejects.toThrow(ApiError);
    await expect(getBranchDetail('BAD')).rejects.toThrow('Not found');
  });

  it('postControl should POST correct payload', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ message: 'OK', new_multiplier: 2.0 }),
    } as Response);

    const res = await postControl({ eps_multiplier: 2.0 });
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/control'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ eps_multiplier: 2.0 }),
      })
    );
    expect(res.new_multiplier).toBe(2.0);
  });
});
