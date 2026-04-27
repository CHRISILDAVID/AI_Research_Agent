import { useState, useRef, useEffect } from 'react';
import {
  Search, Send, Plus, Trash2, Clock, BookOpen,
  Sparkles, Upload, ChevronRight, Globe, FileText
} from 'lucide-react';
import useWebSocket from './hooks/useWebSocket';
import useResearch from './hooks/useResearch';
import AgentStatus from './components/AgentStatus';
import ResearchReport from './components/ResearchReport';
import FileUpload from './components/FileUpload';

function App() {
  const [topic, setTopic] = useState('');
  const [depth, setDepth] = useState('standard');
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [showUpload, setShowUpload] = useState(false);

  const chatEndRef = useRef(null);

  const {
    currentStatus, report, isResearching, events, startResearch: wsStartResearch,
  } = useWebSocket();

  const {
    sessions, listSessions, deleteSession, uploadFile,
  } = useResearch();

  // Load sessions on mount
  useEffect(() => { listSessions(); }, [listSessions]);

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentStatus, report]);

  const handleStartResearch = () => {
    if (!topic.trim() || isResearching) return;

    const sessionId = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
    setActiveSessionId(sessionId);

    // Add user message
    setMessages(prev => [...prev, { type: 'user', content: topic }]);

    // Start WebSocket research
    wsStartResearch(sessionId, topic.trim(), depth);
    setTopic('');

    // Refresh session list after a delay
    setTimeout(() => listSessions(), 2000);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleStartResearch();
    }
  };

  const handleFileUpload = async (file) => {
    if (!activeSessionId) return;
    try {
      const result = await uploadFile(file, activeSessionId);
      setMessages(prev => [...prev, {
        type: 'agent',
        label: 'Document Loader',
        content: `📄 Uploaded **${file.name}** — ${result.result || 'File ready for research'}`,
      }]);
      setShowUpload(false);
    } catch (err) {
      setMessages(prev => [...prev, {
        type: 'agent',
        label: 'Error',
        content: `Failed to upload file: ${err.message}`,
      }]);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    await deleteSession(sessionId);
    if (sessionId === activeSessionId) {
      setActiveSessionId(null);
      setMessages([]);
    }
  };

  const handleNewResearch = () => {
    setActiveSessionId(null);
    setMessages([]);
    setTopic('');
    setShowUpload(false);
  };

  return (
    <div className="app-layout">
      {/* ─── Sidebar ─── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="sidebar-logo-icon">🔬</div>
            <div>
              <h1>Research Agent</h1>
              <p>AI-Powered Research</p>
            </div>
          </div>
        </div>

        <div className="sidebar-content">
          <button className="new-research-btn" onClick={handleNewResearch}>
            <Plus size={16} />
            New Research
          </button>

          <div className="sidebar-section-title">Recent Sessions</div>

          {sessions.length === 0 && (
            <p style={{ fontSize: 12, color: 'var(--text-muted)', padding: '8px 4px' }}>
              No research sessions yet.
            </p>
          )}

          {sessions.map(session => (
            <div
              key={session.session_id}
              className={`session-item ${session.session_id === activeSessionId ? 'active' : ''}`}
              onClick={() => setActiveSessionId(session.session_id)}
            >
              <div className="session-item-topic">{session.topic}</div>
              <div className="session-item-meta">
                <Clock size={10} />
                <span>{new Date(session.created_at).toLocaleDateString()}</span>
                <span style={{
                  marginLeft: 'auto',
                  color: session.status === 'completed' ? 'var(--success)' :
                         session.status === 'failed' ? 'var(--error)' : 'var(--warning)',
                  fontSize: 10,
                  fontWeight: 600,
                }}>
                  {session.status}
                </span>
                <Trash2
                  size={12}
                  style={{ cursor: 'pointer', color: 'var(--text-muted)' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteSession(session.session_id);
                  }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Sidebar Footer */}
        <div style={{
          padding: '16px 20px',
          borderTop: '1px solid var(--border-subtle)',
          fontSize: 11,
          color: 'var(--text-muted)',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}>
          <Sparkles size={12} color="var(--accent-primary)" />
          Powered by LangGraph + Gemini
        </div>
      </aside>

      {/* ─── Main Content ─── */}
      <main className="main-content">
        {/* Header */}
        <div className="content-header">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <BookOpen size={20} color="var(--accent-primary)" />
            {activeSessionId ? `Research: ${messages[0]?.content || 'Session'}` : 'AI Research Agent'}
          </h2>
          <div className="header-status">
            {isResearching && (
              <>
                <div className="status-dot researching" style={{ width: 8, height: 8 }} />
                <span>Researching...</span>
              </>
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className="chat-area">
          {messages.length === 0 && !isResearching ? (
            /* ─── Empty State ─── */
            <div className="empty-state">
              <div className="empty-state-icon">🧠</div>
              <h2>What would you like to research?</h2>
              <p>
                Enter any topic and the AI Research Agent will autonomously search the web,
                analyze information, and generate a comprehensive report with citations.
              </p>
              <div style={{
                display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center',
                marginTop: 8,
              }}>
                {[
                  'Quantum Computing Applications',
                  'CRISPR Gene Therapy 2024',
                  'AI in Drug Discovery',
                ].map(suggestion => (
                  <button
                    key={suggestion}
                    onClick={() => setTopic(suggestion)}
                    style={{
                      padding: '8px 16px',
                      background: 'var(--bg-glass)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-xl)',
                      color: 'var(--text-secondary)',
                      fontFamily: 'var(--font-sans)',
                      fontSize: 13,
                      cursor: 'pointer',
                      transition: 'all var(--transition-fast)',
                    }}
                    onMouseEnter={e => {
                      e.target.style.borderColor = 'var(--accent-primary)';
                      e.target.style.color = 'var(--accent-primary)';
                    }}
                    onMouseLeave={e => {
                      e.target.style.borderColor = 'var(--border-subtle)';
                      e.target.style.color = 'var(--text-secondary)';
                    }}
                  >
                    <Search size={12} style={{ marginRight: 6, verticalAlign: -1 }} />
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {/* Messages */}
              {messages.map((msg, i) => (
                <div key={i} className={`message ${msg.type}`}>
                  {msg.label && <div className="message-label">{msg.label}</div>}
                  <div className="message-content">{msg.content}</div>
                </div>
              ))}

              {/* Agent Status (shown during research) */}
              {isResearching && currentStatus && (
                <AgentStatus status={currentStatus} events={events} />
              )}

              {/* File Upload Zone */}
              {showUpload && (
                <div style={{ animation: 'messageIn 0.3s ease-out' }}>
                  <FileUpload
                    onUpload={handleFileUpload}
                    sessionId={activeSessionId}
                    disabled={!activeSessionId}
                  />
                </div>
              )}

              {/* Research Report */}
              {report && <ResearchReport report={report} />}
            </>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        <div className="input-area">
          <div className="input-wrapper">
            <div className="input-field-container">
              <textarea
                className="input-field"
                placeholder="Enter a research topic..."
                value={topic}
                onChange={e => setTopic(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isResearching}
                rows={1}
              />
            </div>
            <button
              className="send-btn"
              onClick={handleStartResearch}
              disabled={!topic.trim() || isResearching}
              title="Start Research"
            >
              <Send size={18} />
            </button>
          </div>

          <div className="input-options">
            <div className="depth-selector">
              {['quick', 'standard', 'deep'].map(d => (
                <button
                  key={d}
                  className={`depth-option ${depth === d ? 'active' : ''}`}
                  onClick={() => setDepth(d)}
                >
                  {d === 'quick' && '⚡'} {d === 'standard' && '📊'} {d === 'deep' && '🔬'}
                  {' '}{d.charAt(0).toUpperCase() + d.slice(1)}
                </button>
              ))}
            </div>

            <button
              className="upload-btn"
              onClick={() => setShowUpload(!showUpload)}
            >
              <Upload size={12} />
              Upload PDF
            </button>

            <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 'auto' }}>
              <Globe size={10} style={{ verticalAlign: -1, marginRight: 4 }} />
              Tavily Search + ChromaDB RAG
            </span>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
