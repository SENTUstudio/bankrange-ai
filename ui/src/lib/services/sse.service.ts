import { engineState, updateEngineState } from '$lib/state/engineStore.svelte';
import type { EngineStatus } from '$lib/types/engine';

const SSE_URL = import.meta.env.VITE_SSE_URL || '/events/stream';
const INITIAL_RETRY_MS = 3000;
const MAX_RETRY_MS = 30000;

class SseService {
  private es: EventSource | null = null;
  private retryMs = INITIAL_RETRY_MS;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  connect() {
    if (this.es) return; // Already connected
    this._open();
  }

  private _open() {
    try {
      this.es = new EventSource(SSE_URL);

      this.es.onopen = () => {
        this.retryMs = INITIAL_RETRY_MS;
        engineState.sseConnected = true;
      };

      this.es.onmessage = (event) => {
        if (event.data.trim() === '') return; // Heartbeat or empty
        try {
          const payload: EngineStatus = JSON.parse(event.data);
          updateEngineState(payload);
        } catch (err) {
          console.warn('[SSE] Failed to parse message:', err);
        }
      };

      this.es.onerror = () => {
        engineState.sseConnected = false;
        this._scheduleReconnect();
      };
    } catch (err) {
      console.error('[SSE] Failed to create EventSource:', err);
      engineState.sseConnected = false;
      this._scheduleReconnect();
    }
  }

  private _scheduleReconnect() {
    this._close();

    if (this.reconnectTimer) return;

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this._open();
    }, this.retryMs);

    // Exponential backoff capped at MAX_RETRY_MS
    this.retryMs = Math.min(this.retryMs * 2, MAX_RETRY_MS);
  }

  disconnect() {
    this._close();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.retryMs = INITIAL_RETRY_MS;
    engineState.sseConnected = false;
  }

  private _close() {
    if (this.es) {
      this.es.onopen = null;
      this.es.onmessage = null;
      this.es.onerror = null;
      this.es.close();
      this.es = null;
    }
  }

  get connected() {
    return this.es?.readyState === EventSource.OPEN;
  }
}

export const sseService = new SseService();
