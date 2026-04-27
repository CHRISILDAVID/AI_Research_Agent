import { useCallback, useEffect, useRef, useState } from 'react';

const WS_BASE = 'ws://localhost:8000';

/**
 * Custom hook for WebSocket connection to the research backend.
 * Manages connection lifecycle, event streaming, and auto-reconnection.
 */
export default function useWebSocket() {
  const wsRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState([]);
  const [currentStatus, setCurrentStatus] = useState(null);
  const [report, setReport] = useState(null);
  const [isResearching, setIsResearching] = useState(false);

  const connect = useCallback((sessionId) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }

    const ws = new WebSocket(`${WS_BASE}/ws/research/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log('[WS] Connected for session:', sessionId);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setEvents(prev => [...prev, data]);

        switch (data.event) {
          case 'status':
            setCurrentStatus(data.data);
            break;
          case 'agent_step':
            setCurrentStatus(prev => ({ ...prev, ...data.data }));
            break;
          case 'report':
            setReport(data.data);
            setIsResearching(false);
            break;
          case 'complete':
            setIsResearching(false);
            setCurrentStatus(prev => ({ ...prev, status: 'completed' }));
            break;
          case 'error':
            setIsResearching(false);
            setCurrentStatus(prev => ({ ...prev, status: 'error', error: data.data.message }));
            break;
          default:
            break;
        }
      } catch (err) {
        console.error('[WS] Parse error:', err);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('[WS] Disconnected');
    };

    ws.onerror = (err) => {
      console.error('[WS] Error:', err);
      setConnected(false);
    };

    return ws;
  }, []);

  const startResearch = useCallback((sessionId, topic, depth = 'standard') => {
    setEvents([]);
    setReport(null);
    setIsResearching(true);
    setCurrentStatus({ status: 'connecting', topic });

    const ws = connect(sessionId);

    // Wait for connection then send start command
    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({ action: 'start', topic, depth }));
      setCurrentStatus({ status: 'starting', topic, depth });
    };
  }, [connect]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => disconnect();
  }, [disconnect]);

  return {
    connected,
    events,
    currentStatus,
    report,
    isResearching,
    startResearch,
    disconnect,
  };
}
