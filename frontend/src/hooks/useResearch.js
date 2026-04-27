import { useCallback, useState } from 'react';

const API_BASE = 'http://localhost:8000/api';

/**
 * Custom hook for REST API interactions with the research backend.
 */
export default function useResearch() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const startResearch = useCallback(async (topic, depth = 'standard', maxSources = 5) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, depth, max_sources: maxSources }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getSession = useCallback(async (sessionId) => {
    try {
      const res = await fetch(`${API_BASE}/research/${sessionId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      setError(err.message);
      return null;
    }
  }, []);

  const listSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/sessions`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSessions(data.sessions || []);
      return data.sessions;
    } catch (err) {
      setError(err.message);
      return [];
    }
  }, []);

  const deleteSession = useCallback(async (sessionId) => {
    try {
      const res = await fetch(`${API_BASE}/research/${sessionId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setSessions(prev => prev.filter(s => s.session_id !== sessionId));
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  }, []);

  const uploadFile = useCallback(async (file, sessionId = '') => {
    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) formData.append('session_id', sessionId);

    try {
      const res = await fetch(`${API_BASE}/upload?session_id=${sessionId}`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  return {
    sessions,
    loading,
    error,
    startResearch,
    getSession,
    listSessions,
    deleteSession,
    uploadFile,
  };
}
