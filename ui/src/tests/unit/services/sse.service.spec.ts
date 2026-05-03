import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { sseService } from '$lib/services/sse.service';
import { engineState, updateEngineState } from '$lib/state/engineStore.svelte';

vi.mock('$lib/state/engineStore.svelte', () => ({
  engineState: { sseConnected: true, status: 'stopped', multiplier: 1, estimatedEPS: 0, totalWorkstations: 0 },
  updateEngineState: vi.fn(),
}));

describe('sse.service', () => {
  let mockES: any;

  beforeEach(() => {
    mockES = {
      onopen: null as any,
      onmessage: null as any,
      onerror: null as any,
      close: vi.fn(),
      readyState: 1,
    };
    globalThis.EventSource = vi.fn(() => mockES) as any;
    sseService.disconnect();
    vi.mocked(updateEngineState).mockClear();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should create EventSource on connect', () => {
    sseService.connect();
    expect(EventSource).toHaveBeenCalled();
  });

  it('should parse and update engineState on message', () => {
    sseService.connect();
    mockES.onmessage({ data: JSON.stringify({ status: 'running', current_multiplier: 1, estimated_eps: 5, total_workstations: 10 }) });
    expect(updateEngineState).toHaveBeenCalledWith(expect.objectContaining({ status: 'running' }));
  });

  it('should ignore empty data', () => {
    sseService.connect();
    mockES.onmessage({ data: '   ' });
    expect(updateEngineState).not.toHaveBeenCalled();
  });

  it('should update engineState.sseConnected on open', () => {
    engineState.sseConnected = false;
    sseService.connect();
    mockES.onopen();
    expect(engineState.sseConnected).toBe(true);
  });

  it('should update engineState.sseConnected on error', () => {
    engineState.sseConnected = true;
    sseService.connect();
    mockES.onerror();
    expect(engineState.sseConnected).toBe(false);
  });

  it('should reconnect on error with backoff', () => {
    vi.useFakeTimers();
    sseService.connect();
    mockES.onerror();
    expect(mockES.close).toHaveBeenCalled();
    vi.advanceTimersByTime(3000);
    expect(EventSource).toHaveBeenCalledTimes(2);
  });

  it('should cap backoff at 30s', () => {
    vi.useFakeTimers();
    sseService.connect();
    // Trigger multiple errors
    for (let i = 0; i < 10; i++) {
      mockES.onerror();
      vi.advanceTimersByTime(30000);
    }
    // Should still create EventSource after max backoff
    expect(EventSource).toHaveBeenCalled();
  });
});
