import type { EngineStatus } from '$lib/types/engine';

export type SseMessageHandler = (data: EngineStatus) => void;
export type SseConnectionHandler = (connected: boolean) => void;

const SSE_URL = import.meta.env.VITE_SSE_URL || 'http://localhost:8000/events/stream';
const INITIAL_RETRY_MS = 3000;
const MAX_RETRY_MS = 30000;

class SseService {
  private es: EventSource | null = null;
  private retryMs = INITIAL_RETRY_MS;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private _onMessage: SseMessageHandler | null = null;
  private _onConnectionChange: SseConnectionHandler | null = null;

  connect(
    onMessage: SseMessageHandler,
    onConnectionChange?: SseConnectionHandler
  ) {
    if (this.es) return; // Already connected

    this._onMessage = onMessage;
    this._onConnectionChange = onConnectionChange || null;

    this._open();
  }

  private _open() {
    try {
      this.es = new EventSource(SSE_URL);

      this.es.onopen = () => {
        this.retryMs = INITIAL_RETRY_MS;
        this._onConnectionChange?.(true);
      };

      this.es.onmessage = (event) => {
        if (event.data.trim() === '') return; // Heartbeat or empty
        try {
          const payload: EngineStatus = JSON.parse(event.data);
          this._onMessage?.(payload);
        } catch (err) {
          console.warn('[SSE] Failed to parse message:', err);
        }
      };

      this.es.onerror = () => {
        this._onConnectionChange?.(false);
        this._scheduleReconnect();
      };
    } catch (err) {
      console.error('[SSE] Failed to create EventSource:', err);
      this._scheduleReconnect();
    }
  }

  private _scheduleReconnect() {
    this._close(false);

    if (this.reconnectTimer) return;

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this._open();
    }, this.retryMs);

    // Exponential backoff capped at MAX_RETRY_MS
    this.retryMs = Math.min(this.retryMs * 2, MAX_RETRY_MS);
  }

  disconnect() {
    this._close(true);
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.retryMs = INITIAL_RETRY_MS;
  }

  private _close(clearCallbacks: boolean) {
    if (this.es) {
      this.es.onopen = null;
      this.es.onmessage = null;
      this.es.onerror = null;
      this.es.close();
      this.es = null;
    }
    if (clearCallbacks) {
      this._onMessage = null;
      this._onConnectionChange = null;
    }
  }

  get connected() {
    return this.es?.readyState === EventSource.OPEN;
  }
}

export const sseService = new SseService();
