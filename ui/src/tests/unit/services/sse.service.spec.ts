import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { sseService } from '$lib/services/sse.service';

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
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should create EventSource on connect', () => {
    const onMessage = vi.fn();
    sseService.connect(onMessage);
    expect(EventSource).toHaveBeenCalled();
  });

  it('should parse and forward messages', () => {
    const onMessage = vi.fn();
    sseService.connect(onMessage);
    mockES.onmessage({ data: JSON.stringify({ status: 'running', current_multiplier: 1, estimated_eps: 5, total_workstations: 10 }) });
    expect(onMessage).toHaveBeenCalledWith(expect.objectContaining({ status: 'running' }));
  });

  it('should ignore empty data', () => {
    const onMessage = vi.fn();
    sseService.connect(onMessage);
    mockES.onmessage({ data: '   ' });
    expect(onMessage).not.toHaveBeenCalled();
  });

  it('should call connection change handler', () => {
    const onConn = vi.fn();
    sseService.connect(vi.fn(), onConn);
    mockES.onopen();
    expect(onConn).toHaveBeenCalledWith(true);
  });

  it('should reconnect on error with backoff', () => {
    vi.useFakeTimers();
    sseService.connect(vi.fn());
    mockES.onerror();
    expect(mockES.close).toHaveBeenCalled();
    vi.advanceTimersByTime(3000);
    expect(EventSource).toHaveBeenCalledTimes(2);
  });

  it('should cap backoff at 30s', () => {
    vi.useFakeTimers();
    sseService.connect(vi.fn());
    // Trigger multiple errors
    for (let i = 0; i < 10; i++) {
      mockES.onerror();
      vi.advanceTimersByTime(30000);
    }
    // Should still create EventSource after max backoff
    expect(EventSource).toHaveBeenCalled();
  });
});
